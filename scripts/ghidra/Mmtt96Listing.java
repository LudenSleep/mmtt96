// postScript of `db.py listing` (-process -noanalysis -readOnly): one raw listing TSV per region, for db.py to
// translate into AS (asw) text. Args: <ranges tsv (id start end; hex 0x%06X, end exclusive)> <out dir> <ok marker>.
// Out: <out dir>/<id>.tsv, cols `addr len kind text ops targets`:
//   kind insn: text = mnemonic, ops = default operand reprs joined by \u001f, targets = ';'-joined 0x%08X flow
//              targets and operand reference addresses (memory refs only)
//   kind data: one row per maximal run of non-instruction bytes (undefined or defined data), text/ops/targets empty
// An instruction that runs past the region end is emitted as data. Hex 0x%06X addrs, LF, UTF-8; marker written last.
// Holds instruction-form game code: the output stays under .run/ (firewall).
//@category mmtt96
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;

import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;

public class Mmtt96Listing extends GhidraScript {
	static String hex(long a) {
		return String.format("0x%06X", a);
	}

	@Override
	public void run() throws Exception {
		String[] args = getScriptArgs();
		Path out = Paths.get(args[1]);
		Files.createDirectories(out);
		AddressSpace sp = currentProgram.getAddressFactory().getDefaultAddressSpace();
		Listing listing = currentProgram.getListing();
		int regions = 0;
		long insns = 0;
		for (String line : Files.readAllLines(Paths.get(args[0]), StandardCharsets.UTF_8)) {
			if (line.isEmpty()) {
				continue;
			}
			String[] f = line.split("\t");
			String id = f[0];
			long start = Long.decode(f[1]), end = Long.decode(f[2]);
			StringBuilder b = new StringBuilder("addr\tlen\tkind\ttext\tops\ttargets\n");
			long a = start, run = -1;
			while (a < end) {
				Instruction in = listing.getInstructionAt(sp.getAddress(a));
				if (in == null || a + in.getLength() > end) {
					if (run < 0) {
						run = a;
					}
					a++;
					continue;
				}
				if (run >= 0) {
					b.append(hex(run)).append('\t').append(a - run).append("\tdata\t\t\t\n");
					run = -1;
				}
				List<String> ops = new ArrayList<>();
				for (int i = 0; i < in.getNumOperands(); i++) {
					ops.add(in.getDefaultOperandRepresentation(i));
				}
				TreeSet<String> tg = new TreeSet<>();
				for (Address t : in.getFlows()) {
					tg.add(String.format("0x%08X", t.getOffset()));
				}
				for (Reference r : in.getReferencesFrom()) {
					if (r.getToAddress().isMemoryAddress()) {
						tg.add(String.format("0x%08X", r.getToAddress().getOffset()));
					}
				}
				b.append(hex(a)).append('\t').append(in.getLength()).append("\tinsn\t").append(in.getMnemonicString())
					.append('\t').append(String.join("\u001f", ops)).append('\t').append(String.join(";", tg))
					.append('\n');
				insns++;
				a += in.getLength();
			}
			if (run >= 0) {
				b.append(hex(run)).append('\t').append(end - run).append("\tdata\t\t\t\n");
			}
			Files.write(out.resolve(id + ".tsv"), b.toString().getBytes(StandardCharsets.UTF_8));
			regions++;
		}
		Files.writeString(Paths.get(args[2]), "regions " + regions + " insns " + insns + "\n");
		println("mmtt96 listing: regions " + regions + " insns " + insns);
	}
}
