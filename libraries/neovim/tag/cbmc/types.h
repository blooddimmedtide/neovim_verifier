typedef struct {
  // filled in by parse_tag_line():
  char *tagname;        // start of tag name (skip "file:")
  char *tagname_end;    // char after tag name
  char *fname;          // first char of file name
  char *fname_end;      // char after file name
  char *command;        // first char of command
  // filled in by parse_match():
  char *command_end;    // first char after command
  char *tag_fname;      // file name of the tags file. This is used
  // when 'tr' is set.
  char *tagkind;          // "kind:" value
  char *tagkind_end;      // end of tagkind
  char *user_data;        // user_data string
  char *user_data_end;    // end of user_data
  linenr_T tagline;       // "line:" value
} tagptrs_T;
