" 2^31 bytes: ins_typebuf() takes (int)strlen() = INT_MIN
let s = repeat(repeat('a', 65536), 32768)
echo strlen(s)
call feedkeys(s, 'n')
qa!
