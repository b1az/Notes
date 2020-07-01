# Memory

```dos
// 01x xxxxxxxxxxxx = RAM16K
// 1xx xxxxxxxxxxxx = screen
// 110 000000000000 = kbd
DMux(in=load, sel=address[14], a=loadram, b=loadscreen);
RAM16K(in=in, load=loadram, address=address[0..13], out=o1);
Screen(in=in, load=loadscreen, address=address[0..12], out=o2);
Keyboard(out=o3);

Mux8Way16(a=o1,b=o1,c=o1,d=o1, e=o2,f=o2, g=o3, h=false, sel=address[12..14], out=out);
```

# CPU

```dos
// instruction[15] = 0 (A-instruction) or 1 (C-instruction)
Not(in=instruction[15], out=aInst);
Not(in=aInst, out=cInst);

// Destination bits:
// instruction[5]=d1=A
// instruction[4]=d2=D
// instruction[3]=d3=M
// Load A-register on (A-instruction) or (C-instruction and d1 = 1)
And(a=cInst, b=instruction[5], out=loadA2ndCondition);
Or(a=aInst, b=loadA2ndCondition, out=loadA);
// Load D-register on (C-instruction and d2 = 1)
And(a=cInst, b=instruction[4], out=loadD);

// Load A-register with either:
// - previous ALU-output (either for a jump OR A-register as the C-instruction's destination) or
// - new (A- or C-)instruction
Mux16(a=instruction, b=outALU, sel=cInst, out=outMuxA);
ARegister(in=outMuxA, load=loadA, out=outA, out[0..14]=addressM);

// ALU y-input: either A-register or memory data
Mux16(a=outA, b=inM, sel=instruction[12], out=outAorM);
// ALU x-input: either A-register or memory data
DRegister(in=outALU, load=loadD, out=outD);

ALU(x=outD, y=outAorM,
	zx=instruction[11],
    nx=instruction[10],
    zy=instruction[9],
    ny=instruction[8],
     f=instruction[7],
    no=instruction[6],
    out=outALU,
    out=outM,
    zr=zr, ng=ng);

// Write to M when (C-instruction and d3 = 1)
And(a=cInst, b=instruction[3], out=writeM);

// Program counter:
// If any jump bit was set && the jump-condition was satisfied (by ALU's zr and ng bits), load.
// Else, just increment.
And(a=instruction[2], b=ng, out=o1);	// j1 & ng
And(a=instruction[1], b=zr, out=o2);    // j2 & zr
Or(a=ng, b=zr, out=ngORzr);
Not(in=ngORzr, out=NOTngORzr);
And(a=instruction[0], b=NOTngORzr, out=o3);	// j3 & !(ng or zr)
Or8Way(in[0]=o1,in[1]=o2,in[2]=o3, out=o4);
And(a=cInst, b=o4, out=loadPC); // Don't load PC on A-instruction
PC(in=outA, load=loadPC, inc=true, reset=reset, out[0..14]=pc);
```

# Computer

```dos
ROM32K(address=pc, out=instruction);
CPU(inM=inM, instruction=instruction, reset=reset, outM=outM, writeM=writeM, addressM=addressM, pc=pc);
Memory(in=outM, load=writeM, address=addressM, out=inM);
```
