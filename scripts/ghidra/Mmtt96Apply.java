// preScript of the db.py rebuild import: create the Mega Drive blocks and apply config/ghidra/*.tsv before
// auto-analysis. Args: <config dir> <ok marker path> [labels]. The marker is written only when everything applied.
// Two passes (T34.c2): the preScript applies everything except kind=label symbols; the last postScript
// (args ... labels) applies the labels after auto-analysis (and after Mmtt96Seed), so a label never seeds or
// names a function. At an analysis-created default function entry a global label would rename the function
// (SymbolManager.tryUpdatingDefaultFunction): the label is created in the function namespace, then moved to global.
// Non-native columns: symbol source -> user StringPropertyMap mmtt96.symsrc (keyed by addr);
// regions -> mmtt96.region (keyed by start, value end\ttype\tnote).
//@category mmtt96
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;

import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.listing.*;
import ghidra.program.model.mem.*;
import ghidra.program.model.symbol.*;
import ghidra.program.model.util.*;

public class Mmtt96Apply extends GhidraScript {
	// name, start, size; JCART range unverified (docs/ops/ops-setup-decomp.md)
	static final Object[][] BLOCKS = { { "JCART", 0x380000L, 0x80000L }, { "Z80", 0xA00000L, 0x10000L },
		{ "IO", 0xA10000L, 0x10000L }, { "VDP", 0xC00000L, 0x20L }, { "RAM", 0xFF0000L, 0x10000L } };

	List<String[]> read(Path dir, String file, String header) throws Exception {
		List<String> lines = Files.readAllLines(dir.resolve(file), StandardCharsets.UTF_8);
		if (lines.isEmpty() || !lines.get(0).equals(header)) {
			throw new Exception(file + ": bad header");
		}
		int n = header.split("\t").length;
		List<String[]> rows = new ArrayList<>();
		for (String l : lines.subList(1, lines.size())) {
			String[] r = l.split("\t", -1);
			if (r.length != n) {
				throw new Exception(file + ": bad row " + l);
			}
			rows.add(r);
		}
		return rows;
	}

	Address at(String hex) {
		return toAddr(Long.parseLong(hex.substring(2), 16));
	}

	static CommentType ctype(String t) throws Exception {
		switch (t) {
			case "plate": return CommentType.PLATE;
			case "pre": return CommentType.PRE;
			case "eol": return CommentType.EOL;
			case "post": return CommentType.POST;
			case "repeatable": return CommentType.REPEATABLE;
		}
		throw new Exception("bad comment type " + t);
	}

	// postScript pass: kind=label symbols after auto-analysis; marker gets "labels <n>".
	void labels(Path dir, Path marker) throws Exception {
		SymbolTable st = currentProgram.getSymbolTable();
		Listing listing = currentProgram.getListing();
		int nl = 0;
		for (String[] r : read(dir, "symbols.tsv", "addr\tname\tkind\tsource")) {
			if (!r[2].equals("label")) {
				continue;
			}
			Address a = at(r[0]);
			Function f = listing.getFunctionAt(a);
			if (f != null && f.getSymbol().getSource() == SourceType.DEFAULT) {
				st.createLabel(a, r[1], f, SourceType.USER_DEFINED).setNamespace(currentProgram.getGlobalNamespace());
			}
			else {
				st.createLabel(a, r[1], SourceType.USER_DEFINED).setPrimary();
			}
			nl++;
		}
		Files.writeString(marker, "labels " + nl + "\n");
		println("mmtt96 apply: labels " + nl);
	}

	@Override
	public void run() throws Exception {
		String[] args = getScriptArgs();
		Path dir = Paths.get(args[0]);
		if (args.length > 2 && args[2].equals("labels")) {
			labels(dir, Paths.get(args[1]));
			return;
		}
		Memory mem = currentProgram.getMemory();
		MemoryBlock rom = mem.getBlock(toAddr(0));
		if (rom == null || !rom.getName().equals("ROM") || rom.getSize() != 0x100000L) {
			throw new Exception("ROM block must be ROM 0x000000-0x0FFFFF");
		}
		rom.setPermissions(true, false, true);
		for (Object[] b : BLOCKS) {
			MemoryBlock m = mem.createUninitializedBlock((String) b[0], toAddr((Long) b[1]), (Long) b[2], false);
			m.setPermissions(true, true, false);
			m.setVolatile(!b[0].equals("RAM"));
		}
		PropertyMapManager pm = currentProgram.getUsrPropertyManager();
		StringPropertyMap src = pm.createStringPropertyMap("mmtt96.symsrc");
		StringPropertyMap reg = pm.createStringPropertyMap("mmtt96.region");
		SymbolTable st = currentProgram.getSymbolTable();
		Listing listing = currentProgram.getListing();
		int ns = 0, nf = 0, nc = 0, nr = 0;
		for (String[] r : read(dir, "symbols.tsv", "addr\tname\tkind\tsource")) {
			Address a = at(r[0]);
			if (r[2].equals("function")) {
				new DisassembleCommand(a, null, true).applyTo(currentProgram, monitor);
				if (createFunction(a, r[1]) == null) {
					throw new Exception("createFunction failed at " + r[0]);
				}
				nf++;
			}
			src.add(a, r[3]);
			ns++;
		}
		for (String[] r : read(dir, "functions.tsv", "entry\tname")) {
			Function f = listing.getFunctionAt(at(r[0]));
			if (f == null || !f.getName().equals(r[1])) {
				throw new Exception("functions.tsv row not applied: " + r[0] + " " + r[1]);
			}
		}
		for (String[] r : read(dir, "comments.tsv", "addr\ttype\ttext")) {
			listing.setComment(at(r[0]), ctype(r[1]), r[2].replace("\\n", "\n"));
			nc++;
		}
		for (String[] r : read(dir, "regions.tsv", "start\tend\ttype\tnote")) {
			reg.add(at(r[0]), r[1] + "\t" + r[2] + "\t" + r[3]);
			nr++;
		}
		Files.writeString(Paths.get(args[1]),
			"symbols " + ns + " functions " + nf + " comments " + nc + " regions " + nr + "\n");
		println("mmtt96 apply: symbols " + ns + " functions " + nf + " comments " + nc + " regions " + nr);
	}
}
