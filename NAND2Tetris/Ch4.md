# Mult

```dos
@R2
(LOOP) // loop R0-times
M=0
@R0
M=M-1
D=M
@END
D;JLT // R0 < 0?

@R1
D=M
@R2
M=D+M
@LOOP
0;JMP
(END)
@END
0;JMP
```

# Fill

```dos
(KBD_LOOP)
@KBD
D=M
@PAINT
D;JEQ

@8192 // 256 rows, 32 words in each
D=A
(WHITE_LOOP)
        // ...
@WHITE_LOOP
D;JGE
@KBD_LOOP
0;JMP

(PAINT)
@8192 // 256 rows, 32 words in each
D=A
(BLACK_LOOP)
	D=D-1
	@SCREEN
	A=A+D
	M=-1 // Paint it black
@BLACK_LOOP
D;JGE
@KBD_LOOP
0;JMP
```
