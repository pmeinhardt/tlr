{
  function list(first, rest) {
    return [first].concat(rest);
  }
}

start
  = document

document
  = first:line? rest:(eol l:line { return l; })* eol? {
    return list(first, rest).filter(function (e) {
      return e !== null;
    });
  }

line
  = stmt:statement (s comment)? { return stmt ? stmt : null; }
  / comment? { return null; }

statement
  = s:subject s p:predicate s o:object s c:(v:context s { return v; })? "." {
    var stmt = {s: s, p: p, o: o};
    if (c) stmt.c = c;
    return stmt;
  }

subject "subject"
  = iriref
  / bnode

predicate "predicate"
  = iriref

object "object"
  = iriref
  / bnode
  / literal

context "context"
  = iriref
  / bnode

iriref
  = "<" iri:([^\x00-\x20<>"{}|^`\\] / uchar)* ">" {
    return {type: 'iri', value: iri.join('')};
  }

bnode
  = "_:" (pncharsu / [0-9]) pnchars* ("."+ pnchars+)* {
    return {type: 'bnode', value: text()};
  }

literal
  = value:litquote dl:("^^" datatype:iriref / lang:langtag)? {
    var lit = {type: 'literal', value: value};
    if (dl) {
      if (dl.type === 'iri') lit.datatype = dl.value;
      if (typeof dl === 'string') lit.lang = dl;
    }
    return lit;
  }

litquote
  = "\"" chars:([^\x22\x5c\x0a\x0d] / echar / uchar)* "\"" {
    return chars.join('');
  }

langtag
  = "@" first:[a-zA-Z]+ rest:("-" p:[a-zA-Z0-9]+ { return p.join(''); })* {
    return list(first.join(''), rest).join('-');
  }

comment
  = "#" [^\n\r]* {
    return null;
  }

pnchars
  = pncharsu / "-" / [0-9] / [\u00b7] / [\u0300-\u036f] / [\u203F-\u2040]

pncharsu
  = pncharsbase / "_" / ":"

pncharsbase
  = [A-Z] / [a-z] / [\u00C0-\u00d6] / [\u00D8-\u00f6] / [\u00f8-\u02ff]
  / [\u0370-\u037d] / [\u037f-\u1fff] / [\u200C-\u200d] / [\u2070-\u218f]
  / [\u2c00-\u2fef] / [\u3001-\ud7ff] / [\uf900-\ufdcf] / [\ufdf0-\ufffd]
  / [\u10000-\ueffff]

uchar = ("\\u" hex hex hex hex) / ("\\U" hex hex hex hex hex hex hex hex)
echar = "\\" [tbnrf"'\\]
hex = [0-9a-fA-F]

s = [ \t]+
eol = [\n\r]+
