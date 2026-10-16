// postScript of the db.py export (-process -noanalysis -readOnly): write the owned annotations as
// config/ghidra/*.tsv. Args: <out dir> <ok marker path>. Owned = USER_DEFINED/IMPORTED non-default global
// labels and function names, comments of the five types, the mmtt96.* user property maps.
// Deterministic: no timestamps; lines sorted (fixed-width 0x%06X addr first, then remaining columns); LF; UTF-8.
//@category mmtt96
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import java.util.regex.Pattern;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;
import ghidra.program.model.util.*;

public class Mmtt96Export extends GhidraScript {
	static final Pattern DEFAULT_NAME = Pattern.compile(
		"^(FUN|LAB|DAT|SUB|UNK|PTR|EXT|OFF|BYTE|WORD|DWORD|QWORD|STRING|unicode|ds|s|u|switchD|caseD|thunk_FUN)_(.*_)?[0-9a-fA-F]{6,}$");
	static final String[] TYPE_NAMES = { "plate", "pre", "eol", "post", "repeatable" };
	static final CommentType[] TYPES = { CommentType.PLATE, CommentType.PRE, CommentType.EOL,
		CommentType.POST, CommentType.REPEATABLE };

	static String hex(Address a) {
		return String.format("0x%06X", a.getOffset());
	}

	static String field(String s) {
		return s.replace("\r\n", "\\n").replace("\n", "\\n").replace("\r", "\\n").replace("\t", " ");
	}

	static boolean owned(Symbol s) {
		SourceType t = s.getSource();
		return (t == SourceType.USER_DEFINED || t == SourceType.IMPORTED) && !s.isExternal() &&
			s.getParentNamespace().isGlobal() && !DEFAULT_NAME.matcher(s.getName()).matches();
	}

	void write(Path out, String file, String header, List<String> lines) throws Exception {
		Collections.sort(lines);
		StringBuilder b = new StringBuilder(header).append('\n');
		for (String l : lines) {
			b.append(l).append('\n');
		}
		Files.write(out.resolve(file), b.toString().getBytes(StandardCharsets.UTF_8));
	}

	@Override
	public void run() throws Exception {
		String[] args = getScriptArgs();
		Path out = Paths.get(args[0]);
		Files.createDirectories(out);
		PropertyMapManager pm = currentProgram.getUsrPropertyManager();
		StringPropertyMap src = pm.getStringPropertyMap("mmtt96.symsrc");
		StringPropertyMap reg = pm.getStringPropertyMap("mmtt96.region");
		Listing listing = currentProgram.getListing();

		List<String> sym = new ArrayList<>();
		Set<Address> seen = new HashSet<>();
		for (Symbol s : currentProgram.getSymbolTable().getAllSymbols(false)) {
			SymbolType k = s.getSymbolType();
			if ((k != SymbolType.LABEL && k != SymbolType.FUNCTION) || !owned(s)) {
				continue;
			}
			Address a = s.getAddress();
			if (!seen.add(a)) {
				throw new Exception("two owned symbols at " + hex(a) + " (one per address)");
			}
			String so = src == null ? null : src.getString(a);
			sym.add(hex(a) + "\t" + field(s.getName()) + "\t" + (k == SymbolType.FUNCTION ? "function" : "label") +
				"\t" + (so == null ? "manual" : field(so)));
		}

		List<String> fn = new ArrayList<>();
		for (Function f : listing.getFunctions(true)) {
			if (owned(f.getSymbol())) {
				fn.add(hex(f.getEntryPoint()) + "\t" + field(f.getName()));
			}
		}

		List<String> com = new ArrayList<>();
		AddressIterator ai = listing.getCommentAddressIterator(currentProgram.getMemory(), true);
		while (ai.hasNext()) {
			Address a = ai.next();
			for (int i = 0; i < TYPES.length; i++) {
				String c = listing.getComment(TYPES[i], a);
				if (c != null) {
					com.add(hex(a) + "\t" + TYPE_NAMES[i] + "\t" + field(c));
				}
			}
		}

		List<String> rg = new ArrayList<>();
		if (reg != null) {
			AddressIterator ri = reg.getPropertyIterator();
			while (ri.hasNext()) {
				Address a = ri.next();
				rg.add(hex(a) + "\t" + reg.getString(a));
			}
		}

		write(out, "symbols.tsv", "addr\tname\tkind\tsource", sym);
		write(out, "functions.tsv", "entry\tname", fn);
		write(out, "comments.tsv", "addr\ttype\ttext", com);
		write(out, "regions.tsv", "start\tend\ttype\tnote", rg);
		Files.writeString(Paths.get(args[1]), "symbols " + sym.size() + " functions " + fn.size() + " comments " +
			com.size() + " regions " + rg.size() + "\n");
		println("mmtt96 export: symbols " + sym.size() + " functions " + fn.size() + " comments " + com.size() +
			" regions " + rg.size());
	}
}
