// postScript of `db.py analyse`: after auto-analysis, disassemble from every seed (flow), create functions at
// `entry` seeds, re-analyse the changes, then export what the classifier (classify.py merge) needs to <out dir>:
//   functions.tsv  entry name body            body = ';'-joined start-end (end exclusive) ROM ranges
//   insns.tsv      start end                  maximal runs of contiguous instruction bytes in ROM
//   refs.tsv       from to type               references from instructions to ROM; type call|jump|flow|data
//   bad.tsv        addr category              Error bookmarks in ROM (bad instruction, conflicts)
// Args: <seeds tsv (addr kind; kind entry|flow)> <out dir> <ok marker path>. Hex 0x%06X, lines sorted, LF.
//@category mmtt96
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;

import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.app.cmd.function.CreateFunctionCmd;
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.mem.*;
import ghidra.program.model.symbol.*;

public class Mmtt96Seed extends GhidraScript {
	static String hex(long a) {
		return String.format("0x%06X", a);
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
		Path out = Paths.get(args[1]);
		Files.createDirectories(out);
		MemoryBlock rom = currentProgram.getMemory().getBlock("ROM");
		AddressSet romSet = new AddressSet(rom.getStart(), rom.getEnd());
		Listing listing = currentProgram.getListing();
		List<Address> entries = new ArrayList<>();
		int nd = 0;
		for (String l : Files.readAllLines(Paths.get(args[0]), StandardCharsets.UTF_8)) {
			String[] r = l.split("\t");
			if (r.length < 2 || !r[0].startsWith("0x")) {
				continue;
			}
			Address a = toAddr(Long.parseLong(r[0].substring(2), 16));
			if (listing.getInstructionAt(a) == null) {
				new DisassembleCommand(a, null, true).applyTo(currentProgram, monitor);
				nd++;
			}
			if (r[1].equals("entry")) {
				entries.add(a);
			}
		}
		for (Address a : entries) {
			if (listing.getFunctionAt(a) == null && listing.getInstructionAt(a) != null) {
				new CreateFunctionCmd(a).applyTo(currentProgram, monitor);
			}
		}
		analyzeChanges(currentProgram);

		List<String> fn = new ArrayList<>();
		for (Function f : listing.getFunctions(true)) {
			if (!rom.contains(f.getEntryPoint())) {
				continue;
			}
			StringBuilder body = new StringBuilder();
			for (AddressRange ar : f.getBody()) {
				if (body.length() > 0) {
					body.append(';');
				}
				body.append(hex(ar.getMinAddress().getOffset())).append('-').append(hex(ar.getMaxAddress().getOffset() + 1));
			}
			fn.add(hex(f.getEntryPoint().getOffset()) + "\t" + f.getName() + "\t" + body);
		}

		List<String> ins = new ArrayList<>();
		List<String> refs = new ArrayList<>();
		long rs = -1, re = -1;
		InstructionIterator it = listing.getInstructions(romSet, true);
		while (it.hasNext()) {
			Instruction i = it.next();
			long s = i.getMinAddress().getOffset(), e = i.getMaxAddress().getOffset() + 1;
			if (s == re) {
				re = e;
			}
			else {
				if (rs >= 0) {
					ins.add(hex(rs) + "\t" + hex(re));
				}
				rs = s;
				re = e;
			}
			for (Reference r : i.getReferencesFrom()) {
				Address to = r.getToAddress();
				if (!rom.contains(to)) {
					continue;
				}
				RefType t = r.getReferenceType();
				String k = t.isCall() ? "call" : t.isJump() ? "jump" : t.isFlow() ? "flow" : t.isData() ? "data" : null;
				if (k != null) {
					refs.add(hex(s) + "\t" + hex(to.getOffset()) + "\t" + k);
				}
			}
		}
		if (rs >= 0) {
			ins.add(hex(rs) + "\t" + hex(re));
		}

		List<String> bad = new ArrayList<>();
		Iterator<Bookmark> bi = currentProgram.getBookmarkManager().getBookmarksIterator(BookmarkType.ERROR);
		while (bi.hasNext()) {
			Bookmark b = bi.next();
			if (rom.contains(b.getAddress())) {
				bad.add(hex(b.getAddress().getOffset()) + "\t" + b.getCategory().replace("\t", " "));
			}
		}

		write(out, "functions.tsv", "entry\tname\tbody", fn);
		write(out, "insns.tsv", "start\tend", ins);
		write(out, "refs.tsv", "from\tto\ttype", refs);
		write(out, "bad.tsv", "addr\tcategory", bad);
		String msg = "seeds disassembled " + nd + " entries " + entries.size() + " functions " + fn.size() +
			" insn_runs " + ins.size() + " refs " + refs.size() + " bad " + bad.size();
		Files.writeString(Paths.get(args[2]), msg + "\n");
		println("mmtt96 seed: " + msg);
	}
}
