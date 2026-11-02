void f(void){ char b[4] = "ab"; /*@ assert wrong: b[0] == 0; */ }
void g(void){ char b[4] = {'a','b',0,0}; /*@ assert right: b[0] == 'a'; */ }
