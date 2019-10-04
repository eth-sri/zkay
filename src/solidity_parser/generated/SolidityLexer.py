# Generated from /home/nibau/msc-thesis/zkay/src/solidity_parser/Solidity.g4 by ANTLR 4.7.2
from antlr4 import *
from io import StringIO
from typing.io import TextIO
import sys



def serializedATN():
    with StringIO() as buf:
        buf.write("\3\u608b\ua72a\u8133\ub9ed\u417c\u3be7\u7786\u5964\2E")
        buf.write("\u0254\b\1\4\2\t\2\4\3\t\3\4\4\t\4\4\5\t\5\4\6\t\6\4\7")
        buf.write("\t\7\4\b\t\b\4\t\t\t\4\n\t\n\4\13\t\13\4\f\t\f\4\r\t\r")
        buf.write("\4\16\t\16\4\17\t\17\4\20\t\20\4\21\t\21\4\22\t\22\4\23")
        buf.write("\t\23\4\24\t\24\4\25\t\25\4\26\t\26\4\27\t\27\4\30\t\30")
        buf.write("\4\31\t\31\4\32\t\32\4\33\t\33\4\34\t\34\4\35\t\35\4\36")
        buf.write("\t\36\4\37\t\37\4 \t \4!\t!\4\"\t\"\4#\t#\4$\t$\4%\t%")
        buf.write("\4&\t&\4\'\t\'\4(\t(\4)\t)\4*\t*\4+\t+\4,\t,\4-\t-\4.")
        buf.write("\t.\4/\t/\4\60\t\60\4\61\t\61\4\62\t\62\4\63\t\63\4\64")
        buf.write("\t\64\4\65\t\65\4\66\t\66\4\67\t\67\48\t8\49\t9\4:\t:")
        buf.write("\4;\t;\4<\t<\4=\t=\4>\t>\4?\t?\4@\t@\4A\tA\4B\tB\4C\t")
        buf.write("C\4D\tD\4E\tE\4F\tF\3\2\3\2\3\2\3\2\3\2\3\2\3\2\3\3\3")
        buf.write("\3\3\4\3\4\3\5\3\5\3\6\3\6\3\6\3\7\3\7\3\b\3\b\3\t\3\t")
        buf.write("\3\t\3\n\3\n\3\13\3\13\3\13\3\13\3\13\3\13\3\13\3\13\3")
        buf.write("\13\3\f\3\f\3\r\3\r\3\16\3\16\3\16\3\16\3\16\3\16\3\16")
        buf.write("\3\16\3\16\3\16\3\16\3\16\3\17\3\17\3\17\3\17\3\17\3\17")
        buf.write("\3\17\3\17\3\17\3\20\3\20\3\20\3\20\3\20\3\20\3\20\3\20")
        buf.write("\3\21\3\21\3\22\3\22\3\23\3\23\3\24\3\24\3\24\3\24\3\24")
        buf.write("\3\24\3\24\3\24\3\25\3\25\3\25\3\25\3\25\3\26\3\26\3\26")
        buf.write("\3\26\3\26\3\26\3\26\3\26\3\27\3\27\3\30\3\30\3\30\3\31")
        buf.write("\3\31\3\31\3\32\3\32\3\32\3\32\3\32\3\33\3\33\3\33\3\33")
        buf.write("\3\33\3\33\3\34\3\34\3\34\3\34\3\34\3\34\3\34\3\35\3\35")
        buf.write("\3\36\3\36\3\37\3\37\3 \3 \3!\3!\3\"\3\"\3\"\3#\3#\3$")
        buf.write("\3$\3%\3%\3&\3&\3&\3\'\3\'\3\'\3(\3(\3(\3)\3)\3)\3*\3")
        buf.write("*\3+\3+\3,\3,\3-\3-\3-\3-\3-\3.\3.\3.\3/\3/\3/\3/\3\60")
        buf.write("\6\60\u0138\n\60\r\60\16\60\u0139\3\60\3\60\6\60\u013e")
        buf.write("\n\60\r\60\16\60\u013f\3\60\3\60\6\60\u0144\n\60\r\60")
        buf.write("\16\60\u0145\3\61\3\61\3\61\3\61\3\61\3\61\3\61\3\61\3")
        buf.write("\61\5\61\u0151\n\61\3\62\6\62\u0154\n\62\r\62\16\62\u0155")
        buf.write("\3\62\7\62\u0159\n\62\f\62\16\62\u015c\13\62\3\62\3\62")
        buf.write("\6\62\u0160\n\62\r\62\16\62\u0161\5\62\u0164\n\62\3\62")
        buf.write("\3\62\6\62\u0168\n\62\r\62\16\62\u0169\5\62\u016c\n\62")
        buf.write("\3\63\3\63\3\63\3\63\3\63\3\63\3\63\3\63\3\63\3\63\3\63")
        buf.write("\3\63\3\63\3\63\3\63\3\63\3\63\3\63\3\63\3\63\3\63\3\63")
        buf.write("\3\63\3\63\3\63\3\63\3\63\3\63\3\63\3\63\3\63\3\63\3\63")
        buf.write("\3\63\3\63\3\63\3\63\3\63\3\63\3\63\3\63\3\63\3\63\3\63")
        buf.write("\3\63\3\63\3\63\3\63\3\63\3\63\3\63\3\63\3\63\3\63\3\63")
        buf.write("\3\63\3\63\3\63\3\63\3\63\3\63\3\63\3\63\3\63\3\63\3\63")
        buf.write("\3\63\3\63\3\63\3\63\3\63\3\63\3\63\3\63\3\63\3\63\3\63")
        buf.write("\3\63\3\63\3\63\3\63\3\63\3\63\3\63\3\63\3\63\3\63\5\63")
        buf.write("\u01c5\n\63\3\64\3\64\3\64\3\64\3\64\3\64\3\64\3\64\3")
        buf.write("\64\3\64\3\65\3\65\3\65\3\65\3\65\3\65\3\66\3\66\3\66")
        buf.write("\3\66\3\66\3\66\3\66\3\66\3\66\3\67\3\67\3\67\3\67\3\67")
        buf.write("\3\67\3\67\3\67\3\67\38\38\38\38\38\38\38\38\38\39\39")
        buf.write("\39\39\39\39\39\39\3:\3:\3:\3:\3:\3:\3:\3:\3:\3;\3;\3")
        buf.write(";\3;\3;\3;\3;\3;\3<\3<\3<\3<\3<\3<\3<\3<\3=\3=\3=\3=\3")
        buf.write("=\3=\3=\3>\3>\3>\3>\3>\3?\3?\3?\3?\3?\3@\3@\3@\3@\3@\3")
        buf.write("@\3A\3A\7A\u022c\nA\fA\16A\u022f\13A\3B\3B\3C\3C\3D\6")
        buf.write("D\u0236\nD\rD\16D\u0237\3D\3D\3E\3E\3E\3E\7E\u0240\nE")
        buf.write("\fE\16E\u0243\13E\3E\3E\3E\3E\3E\3F\3F\3F\3F\7F\u024e")
        buf.write("\nF\fF\16F\u0251\13F\3F\3F\3\u0241\2G\3\3\5\4\7\5\t\6")
        buf.write("\13\7\r\b\17\t\21\n\23\13\25\f\27\r\31\16\33\17\35\20")
        buf.write("\37\21!\22#\23%\24\'\25)\26+\27-\30/\31\61\32\63\33\65")
        buf.write("\34\67\359\36;\37= ?!A\"C#E$G%I&K\'M(O)Q*S+U,W-Y.[/]\60")
        buf.write("_\61a\62c\63e\64g\65i\66k\67m8o9q:s;u<w=y>{?}@\177A\u0081")
        buf.write("B\u0083\2\u0085\2\u0087C\u0089D\u008bE\3\2\b\3\2\62;\4")
        buf.write("\2GGgg\6\2&&C\\aac|\7\2&&\62;C\\aac|\5\2\13\f\16\17\"")
        buf.write("\"\4\2\f\f\17\17\2\u026f\2\3\3\2\2\2\2\5\3\2\2\2\2\7\3")
        buf.write("\2\2\2\2\t\3\2\2\2\2\13\3\2\2\2\2\r\3\2\2\2\2\17\3\2\2")
        buf.write("\2\2\21\3\2\2\2\2\23\3\2\2\2\2\25\3\2\2\2\2\27\3\2\2\2")
        buf.write("\2\31\3\2\2\2\2\33\3\2\2\2\2\35\3\2\2\2\2\37\3\2\2\2\2")
        buf.write("!\3\2\2\2\2#\3\2\2\2\2%\3\2\2\2\2\'\3\2\2\2\2)\3\2\2\2")
        buf.write("\2+\3\2\2\2\2-\3\2\2\2\2/\3\2\2\2\2\61\3\2\2\2\2\63\3")
        buf.write("\2\2\2\2\65\3\2\2\2\2\67\3\2\2\2\29\3\2\2\2\2;\3\2\2\2")
        buf.write("\2=\3\2\2\2\2?\3\2\2\2\2A\3\2\2\2\2C\3\2\2\2\2E\3\2\2")
        buf.write("\2\2G\3\2\2\2\2I\3\2\2\2\2K\3\2\2\2\2M\3\2\2\2\2O\3\2")
        buf.write("\2\2\2Q\3\2\2\2\2S\3\2\2\2\2U\3\2\2\2\2W\3\2\2\2\2Y\3")
        buf.write("\2\2\2\2[\3\2\2\2\2]\3\2\2\2\2_\3\2\2\2\2a\3\2\2\2\2c")
        buf.write("\3\2\2\2\2e\3\2\2\2\2g\3\2\2\2\2i\3\2\2\2\2k\3\2\2\2\2")
        buf.write("m\3\2\2\2\2o\3\2\2\2\2q\3\2\2\2\2s\3\2\2\2\2u\3\2\2\2")
        buf.write("\2w\3\2\2\2\2y\3\2\2\2\2{\3\2\2\2\2}\3\2\2\2\2\177\3\2")
        buf.write("\2\2\2\u0081\3\2\2\2\2\u0087\3\2\2\2\2\u0089\3\2\2\2\2")
        buf.write("\u008b\3\2\2\2\3\u008d\3\2\2\2\5\u0094\3\2\2\2\7\u0096")
        buf.write("\3\2\2\2\t\u0098\3\2\2\2\13\u009a\3\2\2\2\r\u009d\3\2")
        buf.write("\2\2\17\u009f\3\2\2\2\21\u00a1\3\2\2\2\23\u00a4\3\2\2")
        buf.write("\2\25\u00a6\3\2\2\2\27\u00af\3\2\2\2\31\u00b1\3\2\2\2")
        buf.write("\33\u00b3\3\2\2\2\35\u00bf\3\2\2\2\37\u00c8\3\2\2\2!\u00d0")
        buf.write("\3\2\2\2#\u00d2\3\2\2\2%\u00d4\3\2\2\2\'\u00d6\3\2\2\2")
        buf.write(")\u00de\3\2\2\2+\u00e3\3\2\2\2-\u00eb\3\2\2\2/\u00ed\3")
        buf.write("\2\2\2\61\u00f0\3\2\2\2\63\u00f3\3\2\2\2\65\u00f8\3\2")
        buf.write("\2\2\67\u00fe\3\2\2\29\u0105\3\2\2\2;\u0107\3\2\2\2=\u0109")
        buf.write("\3\2\2\2?\u010b\3\2\2\2A\u010d\3\2\2\2C\u010f\3\2\2\2")
        buf.write("E\u0112\3\2\2\2G\u0114\3\2\2\2I\u0116\3\2\2\2K\u0118\3")
        buf.write("\2\2\2M\u011b\3\2\2\2O\u011e\3\2\2\2Q\u0121\3\2\2\2S\u0124")
        buf.write("\3\2\2\2U\u0126\3\2\2\2W\u0128\3\2\2\2Y\u012a\3\2\2\2")
        buf.write("[\u012f\3\2\2\2]\u0132\3\2\2\2_\u0137\3\2\2\2a\u0150\3")
        buf.write("\2\2\2c\u0163\3\2\2\2e\u01c4\3\2\2\2g\u01c6\3\2\2\2i\u01d0")
        buf.write("\3\2\2\2k\u01d6\3\2\2\2m\u01df\3\2\2\2o\u01e8\3\2\2\2")
        buf.write("q\u01f1\3\2\2\2s\u01f9\3\2\2\2u\u0202\3\2\2\2w\u020a\3")
        buf.write("\2\2\2y\u0212\3\2\2\2{\u0219\3\2\2\2}\u021e\3\2\2\2\177")
        buf.write("\u0223\3\2\2\2\u0081\u0229\3\2\2\2\u0083\u0230\3\2\2\2")
        buf.write("\u0085\u0232\3\2\2\2\u0087\u0235\3\2\2\2\u0089\u023b\3")
        buf.write("\2\2\2\u008b\u0249\3\2\2\2\u008d\u008e\7r\2\2\u008e\u008f")
        buf.write("\7t\2\2\u008f\u0090\7c\2\2\u0090\u0091\7i\2\2\u0091\u0092")
        buf.write("\7o\2\2\u0092\u0093\7c\2\2\u0093\4\3\2\2\2\u0094\u0095")
        buf.write("\7=\2\2\u0095\6\3\2\2\2\u0096\u0097\7`\2\2\u0097\b\3\2")
        buf.write("\2\2\u0098\u0099\7\u0080\2\2\u0099\n\3\2\2\2\u009a\u009b")
        buf.write("\7@\2\2\u009b\u009c\7?\2\2\u009c\f\3\2\2\2\u009d\u009e")
        buf.write("\7@\2\2\u009e\16\3\2\2\2\u009f\u00a0\7>\2\2\u00a0\20\3")
        buf.write("\2\2\2\u00a1\u00a2\7>\2\2\u00a2\u00a3\7?\2\2\u00a3\22")
        buf.write("\3\2\2\2\u00a4\u00a5\7?\2\2\u00a5\24\3\2\2\2\u00a6\u00a7")
        buf.write("\7e\2\2\u00a7\u00a8\7q\2\2\u00a8\u00a9\7p\2\2\u00a9\u00aa")
        buf.write("\7v\2\2\u00aa\u00ab\7t\2\2\u00ab\u00ac\7c\2\2\u00ac\u00ad")
        buf.write("\7e\2\2\u00ad\u00ae\7v\2\2\u00ae\26\3\2\2\2\u00af\u00b0")
        buf.write("\7}\2\2\u00b0\30\3\2\2\2\u00b1\u00b2\7\177\2\2\u00b2\32")
        buf.write("\3\2\2\2\u00b3\u00b4\7e\2\2\u00b4\u00b5\7q\2\2\u00b5\u00b6")
        buf.write("\7p\2\2\u00b6\u00b7\7u\2\2\u00b7\u00b8\7v\2\2\u00b8\u00b9")
        buf.write("\7t\2\2\u00b9\u00ba\7w\2\2\u00ba\u00bb\7e\2\2\u00bb\u00bc")
        buf.write("\7v\2\2\u00bc\u00bd\7q\2\2\u00bd\u00be\7t\2\2\u00be\34")
        buf.write("\3\2\2\2\u00bf\u00c0\7h\2\2\u00c0\u00c1\7w\2\2\u00c1\u00c2")
        buf.write("\7p\2\2\u00c2\u00c3\7e\2\2\u00c3\u00c4\7v\2\2\u00c4\u00c5")
        buf.write("\7k\2\2\u00c5\u00c6\7q\2\2\u00c6\u00c7\7p\2\2\u00c7\36")
        buf.write("\3\2\2\2\u00c8\u00c9\7t\2\2\u00c9\u00ca\7g\2\2\u00ca\u00cb")
        buf.write("\7v\2\2\u00cb\u00cc\7w\2\2\u00cc\u00cd\7t\2\2\u00cd\u00ce")
        buf.write("\7p\2\2\u00ce\u00cf\7u\2\2\u00cf \3\2\2\2\u00d0\u00d1")
        buf.write("\7*\2\2\u00d1\"\3\2\2\2\u00d2\u00d3\7.\2\2\u00d3$\3\2")
        buf.write("\2\2\u00d4\u00d5\7+\2\2\u00d5&\3\2\2\2\u00d6\u00d7\7c")
        buf.write("\2\2\u00d7\u00d8\7f\2\2\u00d8\u00d9\7f\2\2\u00d9\u00da")
        buf.write("\7t\2\2\u00da\u00db\7g\2\2\u00db\u00dc\7u\2\2\u00dc\u00dd")
        buf.write("\7u\2\2\u00dd(\3\2\2\2\u00de\u00df\7d\2\2\u00df\u00e0")
        buf.write("\7q\2\2\u00e0\u00e1\7q\2\2\u00e1\u00e2\7n\2\2\u00e2*\3")
        buf.write("\2\2\2\u00e3\u00e4\7o\2\2\u00e4\u00e5\7c\2\2\u00e5\u00e6")
        buf.write("\7r\2\2\u00e6\u00e7\7r\2\2\u00e7\u00e8\7k\2\2\u00e8\u00e9")
        buf.write("\7p\2\2\u00e9\u00ea\7i\2\2\u00ea,\3\2\2\2\u00eb\u00ec")
        buf.write("\7#\2\2\u00ec.\3\2\2\2\u00ed\u00ee\7?\2\2\u00ee\u00ef")
        buf.write("\7@\2\2\u00ef\60\3\2\2\2\u00f0\u00f1\7k\2\2\u00f1\u00f2")
        buf.write("\7h\2\2\u00f2\62\3\2\2\2\u00f3\u00f4\7g\2\2\u00f4\u00f5")
        buf.write("\7n\2\2\u00f5\u00f6\7u\2\2\u00f6\u00f7\7g\2\2\u00f7\64")
        buf.write("\3\2\2\2\u00f8\u00f9\7y\2\2\u00f9\u00fa\7j\2\2\u00fa\u00fb")
        buf.write("\7k\2\2\u00fb\u00fc\7n\2\2\u00fc\u00fd\7g\2\2\u00fd\66")
        buf.write("\3\2\2\2\u00fe\u00ff\7t\2\2\u00ff\u0100\7g\2\2\u0100\u0101")
        buf.write("\7v\2\2\u0101\u0102\7w\2\2\u0102\u0103\7t\2\2\u0103\u0104")
        buf.write("\7p\2\2\u01048\3\2\2\2\u0105\u0106\7]\2\2\u0106:\3\2\2")
        buf.write("\2\u0107\u0108\7_\2\2\u0108<\3\2\2\2\u0109\u010a\7\60")
        buf.write("\2\2\u010a>\3\2\2\2\u010b\u010c\7-\2\2\u010c@\3\2\2\2")
        buf.write("\u010d\u010e\7/\2\2\u010eB\3\2\2\2\u010f\u0110\7,\2\2")
        buf.write("\u0110\u0111\7,\2\2\u0111D\3\2\2\2\u0112\u0113\7,\2\2")
        buf.write("\u0113F\3\2\2\2\u0114\u0115\7\61\2\2\u0115H\3\2\2\2\u0116")
        buf.write("\u0117\7\'\2\2\u0117J\3\2\2\2\u0118\u0119\7?\2\2\u0119")
        buf.write("\u011a\7?\2\2\u011aL\3\2\2\2\u011b\u011c\7#\2\2\u011c")
        buf.write("\u011d\7?\2\2\u011dN\3\2\2\2\u011e\u011f\7(\2\2\u011f")
        buf.write("\u0120\7(\2\2\u0120P\3\2\2\2\u0121\u0122\7~\2\2\u0122")
        buf.write("\u0123\7~\2\2\u0123R\3\2\2\2\u0124\u0125\7A\2\2\u0125")
        buf.write("T\3\2\2\2\u0126\u0127\7<\2\2\u0127V\3\2\2\2\u0128\u0129")
        buf.write("\7B\2\2\u0129X\3\2\2\2\u012a\u012b\7w\2\2\u012b\u012c")
        buf.write("\7k\2\2\u012c\u012d\7p\2\2\u012d\u012e\7v\2\2\u012eZ\3")
        buf.write("\2\2\2\u012f\u0130\7o\2\2\u0130\u0131\7g\2\2\u0131\\\3")
        buf.write("\2\2\2\u0132\u0133\7c\2\2\u0133\u0134\7n\2\2\u0134\u0135")
        buf.write("\7n\2\2\u0135^\3\2\2\2\u0136\u0138\t\2\2\2\u0137\u0136")
        buf.write("\3\2\2\2\u0138\u0139\3\2\2\2\u0139\u0137\3\2\2\2\u0139")
        buf.write("\u013a\3\2\2\2\u013a\u013b\3\2\2\2\u013b\u013d\7\60\2")
        buf.write("\2\u013c\u013e\t\2\2\2\u013d\u013c\3\2\2\2\u013e\u013f")
        buf.write("\3\2\2\2\u013f\u013d\3\2\2\2\u013f\u0140\3\2\2\2\u0140")
        buf.write("\u0141\3\2\2\2\u0141\u0143\7\60\2\2\u0142\u0144\t\2\2")
        buf.write("\2\u0143\u0142\3\2\2\2\u0144\u0145\3\2\2\2\u0145\u0143")
        buf.write("\3\2\2\2\u0145\u0146\3\2\2\2\u0146`\3\2\2\2\u0147\u0148")
        buf.write("\7v\2\2\u0148\u0149\7t\2\2\u0149\u014a\7w\2\2\u014a\u0151")
        buf.write("\7g\2\2\u014b\u014c\7h\2\2\u014c\u014d\7c\2\2\u014d\u014e")
        buf.write("\7n\2\2\u014e\u014f\7u\2\2\u014f\u0151\7g\2\2\u0150\u0147")
        buf.write("\3\2\2\2\u0150\u014b\3\2\2\2\u0151b\3\2\2\2\u0152\u0154")
        buf.write("\t\2\2\2\u0153\u0152\3\2\2\2\u0154\u0155\3\2\2\2\u0155")
        buf.write("\u0153\3\2\2\2\u0155\u0156\3\2\2\2\u0156\u0164\3\2\2\2")
        buf.write("\u0157\u0159\t\2\2\2\u0158\u0157\3\2\2\2\u0159\u015c\3")
        buf.write("\2\2\2\u015a\u0158\3\2\2\2\u015a\u015b\3\2\2\2\u015b\u015d")
        buf.write("\3\2\2\2\u015c\u015a\3\2\2\2\u015d\u015f\7\60\2\2\u015e")
        buf.write("\u0160\t\2\2\2\u015f\u015e\3\2\2\2\u0160\u0161\3\2\2\2")
        buf.write("\u0161\u015f\3\2\2\2\u0161\u0162\3\2\2\2\u0162\u0164\3")
        buf.write("\2\2\2\u0163\u0153\3\2\2\2\u0163\u015a\3\2\2\2\u0164\u016b")
        buf.write("\3\2\2\2\u0165\u0167\t\3\2\2\u0166\u0168\t\2\2\2\u0167")
        buf.write("\u0166\3\2\2\2\u0168\u0169\3\2\2\2\u0169\u0167\3\2\2\2")
        buf.write("\u0169\u016a\3\2\2\2\u016a\u016c\3\2\2\2\u016b\u0165\3")
        buf.write("\2\2\2\u016b\u016c\3\2\2\2\u016cd\3\2\2\2\u016d\u016e")
        buf.write("\7c\2\2\u016e\u016f\7d\2\2\u016f\u0170\7u\2\2\u0170\u0171")
        buf.write("\7v\2\2\u0171\u0172\7t\2\2\u0172\u0173\7c\2\2\u0173\u0174")
        buf.write("\7e\2\2\u0174\u01c5\7v\2\2\u0175\u0176\7c\2\2\u0176\u0177")
        buf.write("\7h\2\2\u0177\u0178\7v\2\2\u0178\u0179\7g\2\2\u0179\u01c5")
        buf.write("\7t\2\2\u017a\u017b\7e\2\2\u017b\u017c\7c\2\2\u017c\u017d")
        buf.write("\7u\2\2\u017d\u01c5\7g\2\2\u017e\u017f\7e\2\2\u017f\u0180")
        buf.write("\7c\2\2\u0180\u0181\7v\2\2\u0181\u0182\7e\2\2\u0182\u01c5")
        buf.write("\7j\2\2\u0183\u0184\7f\2\2\u0184\u0185\7g\2\2\u0185\u0186")
        buf.write("\7h\2\2\u0186\u0187\7c\2\2\u0187\u0188\7w\2\2\u0188\u0189")
        buf.write("\7n\2\2\u0189\u01c5\7v\2\2\u018a\u018b\7k\2\2\u018b\u01c5")
        buf.write("\7p\2\2\u018c\u018d\7k\2\2\u018d\u018e\7p\2\2\u018e\u018f")
        buf.write("\7n\2\2\u018f\u0190\7k\2\2\u0190\u0191\7p\2\2\u0191\u01c5")
        buf.write("\7g\2\2\u0192\u0193\7n\2\2\u0193\u0194\7g\2\2\u0194\u01c5")
        buf.write("\7v\2\2\u0195\u0196\7o\2\2\u0196\u0197\7c\2\2\u0197\u0198")
        buf.write("\7v\2\2\u0198\u0199\7e\2\2\u0199\u01c5\7j\2\2\u019a\u019b")
        buf.write("\7p\2\2\u019b\u019c\7w\2\2\u019c\u019d\7n\2\2\u019d\u01c5")
        buf.write("\7n\2\2\u019e\u019f\7q\2\2\u019f\u01c5\7h\2\2\u01a0\u01a1")
        buf.write("\7t\2\2\u01a1\u01a2\7g\2\2\u01a2\u01a3\7n\2\2\u01a3\u01a4")
        buf.write("\7q\2\2\u01a4\u01a5\7e\2\2\u01a5\u01a6\7c\2\2\u01a6\u01a7")
        buf.write("\7v\2\2\u01a7\u01a8\7c\2\2\u01a8\u01a9\7d\2\2\u01a9\u01aa")
        buf.write("\7n\2\2\u01aa\u01c5\7g\2\2\u01ab\u01ac\7u\2\2\u01ac\u01ad")
        buf.write("\7v\2\2\u01ad\u01ae\7c\2\2\u01ae\u01af\7v\2\2\u01af\u01b0")
        buf.write("\7k\2\2\u01b0\u01c5\7e\2\2\u01b1\u01b2\7u\2\2\u01b2\u01b3")
        buf.write("\7y\2\2\u01b3\u01b4\7k\2\2\u01b4\u01b5\7v\2\2\u01b5\u01b6")
        buf.write("\7e\2\2\u01b6\u01c5\7j\2\2\u01b7\u01b8\7v\2\2\u01b8\u01b9")
        buf.write("\7t\2\2\u01b9\u01c5\7{\2\2\u01ba\u01bb\7v\2\2\u01bb\u01bc")
        buf.write("\7{\2\2\u01bc\u01bd\7r\2\2\u01bd\u01c5\7g\2\2\u01be\u01bf")
        buf.write("\7v\2\2\u01bf\u01c0\7{\2\2\u01c0\u01c1\7r\2\2\u01c1\u01c2")
        buf.write("\7g\2\2\u01c2\u01c3\7q\2\2\u01c3\u01c5\7h\2\2\u01c4\u016d")
        buf.write("\3\2\2\2\u01c4\u0175\3\2\2\2\u01c4\u017a\3\2\2\2\u01c4")
        buf.write("\u017e\3\2\2\2\u01c4\u0183\3\2\2\2\u01c4\u018a\3\2\2\2")
        buf.write("\u01c4\u018c\3\2\2\2\u01c4\u0192\3\2\2\2\u01c4\u0195\3")
        buf.write("\2\2\2\u01c4\u019a\3\2\2\2\u01c4\u019e\3\2\2\2\u01c4\u01a0")
        buf.write("\3\2\2\2\u01c4\u01ab\3\2\2\2\u01c4\u01b1\3\2\2\2\u01c4")
        buf.write("\u01b7\3\2\2\2\u01c4\u01ba\3\2\2\2\u01c4\u01be\3\2\2\2")
        buf.write("\u01c5f\3\2\2\2\u01c6\u01c7\7c\2\2\u01c7\u01c8\7p\2\2")
        buf.write("\u01c8\u01c9\7q\2\2\u01c9\u01ca\7p\2\2\u01ca\u01cb\7{")
        buf.write("\2\2\u01cb\u01cc\7o\2\2\u01cc\u01cd\7q\2\2\u01cd\u01ce")
        buf.write("\7w\2\2\u01ce\u01cf\7u\2\2\u01cfh\3\2\2\2\u01d0\u01d1")
        buf.write("\7d\2\2\u01d1\u01d2\7t\2\2\u01d2\u01d3\7g\2\2\u01d3\u01d4")
        buf.write("\7c\2\2\u01d4\u01d5\7m\2\2\u01d5j\3\2\2\2\u01d6\u01d7")
        buf.write("\7e\2\2\u01d7\u01d8\7q\2\2\u01d8\u01d9\7p\2\2\u01d9\u01da")
        buf.write("\7u\2\2\u01da\u01db\7v\2\2\u01db\u01dc\7c\2\2\u01dc\u01dd")
        buf.write("\7p\2\2\u01dd\u01de\7v\2\2\u01del\3\2\2\2\u01df\u01e0")
        buf.write("\7e\2\2\u01e0\u01e1\7q\2\2\u01e1\u01e2\7p\2\2\u01e2\u01e3")
        buf.write("\7v\2\2\u01e3\u01e4\7k\2\2\u01e4\u01e5\7p\2\2\u01e5\u01e6")
        buf.write("\7w\2\2\u01e6\u01e7\7g\2\2\u01e7n\3\2\2\2\u01e8\u01e9")
        buf.write("\7g\2\2\u01e9\u01ea\7z\2\2\u01ea\u01eb\7v\2\2\u01eb\u01ec")
        buf.write("\7g\2\2\u01ec\u01ed\7t\2\2\u01ed\u01ee\7p\2\2\u01ee\u01ef")
        buf.write("\7c\2\2\u01ef\u01f0\7n\2\2\u01f0p\3\2\2\2\u01f1\u01f2")
        buf.write("\7k\2\2\u01f2\u01f3\7p\2\2\u01f3\u01f4\7f\2\2\u01f4\u01f5")
        buf.write("\7g\2\2\u01f5\u01f6\7z\2\2\u01f6\u01f7\7g\2\2\u01f7\u01f8")
        buf.write("\7f\2\2\u01f8r\3\2\2\2\u01f9\u01fa\7k\2\2\u01fa\u01fb")
        buf.write("\7p\2\2\u01fb\u01fc\7v\2\2\u01fc\u01fd\7g\2\2\u01fd\u01fe")
        buf.write("\7t\2\2\u01fe\u01ff\7p\2\2\u01ff\u0200\7c\2\2\u0200\u0201")
        buf.write("\7n\2\2\u0201t\3\2\2\2\u0202\u0203\7r\2\2\u0203\u0204")
        buf.write("\7c\2\2\u0204\u0205\7{\2\2\u0205\u0206\7c\2\2\u0206\u0207")
        buf.write("\7d\2\2\u0207\u0208\7n\2\2\u0208\u0209\7g\2\2\u0209v\3")
        buf.write("\2\2\2\u020a\u020b\7r\2\2\u020b\u020c\7t\2\2\u020c\u020d")
        buf.write("\7k\2\2\u020d\u020e\7x\2\2\u020e\u020f\7c\2\2\u020f\u0210")
        buf.write("\7v\2\2\u0210\u0211\7g\2\2\u0211x\3\2\2\2\u0212\u0213")
        buf.write("\7r\2\2\u0213\u0214\7w\2\2\u0214\u0215\7d\2\2\u0215\u0216")
        buf.write("\7n\2\2\u0216\u0217\7k\2\2\u0217\u0218\7e\2\2\u0218z\3")
        buf.write("\2\2\2\u0219\u021a\7r\2\2\u021a\u021b\7w\2\2\u021b\u021c")
        buf.write("\7t\2\2\u021c\u021d\7g\2\2\u021d|\3\2\2\2\u021e\u021f")
        buf.write("\7x\2\2\u021f\u0220\7k\2\2\u0220\u0221\7g\2\2\u0221\u0222")
        buf.write("\7y\2\2\u0222~\3\2\2\2\u0223\u0224\7h\2\2\u0224\u0225")
        buf.write("\7k\2\2\u0225\u0226\7p\2\2\u0226\u0227\7c\2\2\u0227\u0228")
        buf.write("\7n\2\2\u0228\u0080\3\2\2\2\u0229\u022d\5\u0083B\2\u022a")
        buf.write("\u022c\5\u0085C\2\u022b\u022a\3\2\2\2\u022c\u022f\3\2")
        buf.write("\2\2\u022d\u022b\3\2\2\2\u022d\u022e\3\2\2\2\u022e\u0082")
        buf.write("\3\2\2\2\u022f\u022d\3\2\2\2\u0230\u0231\t\4\2\2\u0231")
        buf.write("\u0084\3\2\2\2\u0232\u0233\t\5\2\2\u0233\u0086\3\2\2\2")
        buf.write("\u0234\u0236\t\6\2\2\u0235\u0234\3\2\2\2\u0236\u0237\3")
        buf.write("\2\2\2\u0237\u0235\3\2\2\2\u0237\u0238\3\2\2\2\u0238\u0239")
        buf.write("\3\2\2\2\u0239\u023a\bD\2\2\u023a\u0088\3\2\2\2\u023b")
        buf.write("\u023c\7\61\2\2\u023c\u023d\7,\2\2\u023d\u0241\3\2\2\2")
        buf.write("\u023e\u0240\13\2\2\2\u023f\u023e\3\2\2\2\u0240\u0243")
        buf.write("\3\2\2\2\u0241\u0242\3\2\2\2\u0241\u023f\3\2\2\2\u0242")
        buf.write("\u0244\3\2\2\2\u0243\u0241\3\2\2\2\u0244\u0245\7,\2\2")
        buf.write("\u0245\u0246\7\61\2\2\u0246\u0247\3\2\2\2\u0247\u0248")
        buf.write("\bE\2\2\u0248\u008a\3\2\2\2\u0249\u024a\7\61\2\2\u024a")
        buf.write("\u024b\7\61\2\2\u024b\u024f\3\2\2\2\u024c\u024e\n\7\2")
        buf.write("\2\u024d\u024c\3\2\2\2\u024e\u0251\3\2\2\2\u024f\u024d")
        buf.write("\3\2\2\2\u024f\u0250\3\2\2\2\u0250\u0252\3\2\2\2\u0251")
        buf.write("\u024f\3\2\2\2\u0252\u0253\bF\2\2\u0253\u008c\3\2\2\2")
        buf.write("\22\2\u0139\u013f\u0145\u0150\u0155\u015a\u0161\u0163")
        buf.write("\u0169\u016b\u01c4\u022d\u0237\u0241\u024f\3\2\3\2")
        return buf.getvalue()


class SolidityLexer(Lexer):

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    T__0 = 1
    T__1 = 2
    T__2 = 3
    T__3 = 4
    T__4 = 5
    T__5 = 6
    T__6 = 7
    T__7 = 8
    T__8 = 9
    T__9 = 10
    T__10 = 11
    T__11 = 12
    T__12 = 13
    T__13 = 14
    T__14 = 15
    T__15 = 16
    T__16 = 17
    T__17 = 18
    T__18 = 19
    T__19 = 20
    T__20 = 21
    T__21 = 22
    T__22 = 23
    T__23 = 24
    T__24 = 25
    T__25 = 26
    T__26 = 27
    T__27 = 28
    T__28 = 29
    T__29 = 30
    T__30 = 31
    T__31 = 32
    T__32 = 33
    T__33 = 34
    T__34 = 35
    T__35 = 36
    T__36 = 37
    T__37 = 38
    T__38 = 39
    T__39 = 40
    T__40 = 41
    T__41 = 42
    T__42 = 43
    Uint = 44
    MeKeyword = 45
    AllKeyword = 46
    VersionLiteral = 47
    BooleanLiteral = 48
    DecimalNumber = 49
    ReservedKeyword = 50
    AnonymousKeyword = 51
    BreakKeyword = 52
    ConstantKeyword = 53
    ContinueKeyword = 54
    ExternalKeyword = 55
    IndexedKeyword = 56
    InternalKeyword = 57
    PayableKeyword = 58
    PrivateKeyword = 59
    PublicKeyword = 60
    PureKeyword = 61
    ViewKeyword = 62
    FinalKeyword = 63
    Identifier = 64
    WS = 65
    COMMENT = 66
    LINE_COMMENT = 67

    channelNames = [ u"DEFAULT_TOKEN_CHANNEL", u"HIDDEN" ]

    modeNames = [ "DEFAULT_MODE" ]

    literalNames = [ "<INVALID>",
            "'pragma'", "';'", "'^'", "'~'", "'>='", "'>'", "'<'", "'<='", 
            "'='", "'contract'", "'{'", "'}'", "'constructor'", "'function'", 
            "'returns'", "'('", "','", "')'", "'address'", "'bool'", "'mapping'", 
            "'!'", "'=>'", "'if'", "'else'", "'while'", "'return'", "'['", 
            "']'", "'.'", "'+'", "'-'", "'**'", "'*'", "'/'", "'%'", "'=='", 
            "'!='", "'&&'", "'||'", "'?'", "':'", "'@'", "'uint'", "'me'", 
            "'all'", "'anonymous'", "'break'", "'constant'", "'continue'", 
            "'external'", "'indexed'", "'internal'", "'payable'", "'private'", 
            "'public'", "'pure'", "'view'", "'final'" ]

    symbolicNames = [ "<INVALID>",
            "Uint", "MeKeyword", "AllKeyword", "VersionLiteral", "BooleanLiteral", 
            "DecimalNumber", "ReservedKeyword", "AnonymousKeyword", "BreakKeyword", 
            "ConstantKeyword", "ContinueKeyword", "ExternalKeyword", "IndexedKeyword", 
            "InternalKeyword", "PayableKeyword", "PrivateKeyword", "PublicKeyword", 
            "PureKeyword", "ViewKeyword", "FinalKeyword", "Identifier", 
            "WS", "COMMENT", "LINE_COMMENT" ]

    ruleNames = [ "T__0", "T__1", "T__2", "T__3", "T__4", "T__5", "T__6", 
                  "T__7", "T__8", "T__9", "T__10", "T__11", "T__12", "T__13", 
                  "T__14", "T__15", "T__16", "T__17", "T__18", "T__19", 
                  "T__20", "T__21", "T__22", "T__23", "T__24", "T__25", 
                  "T__26", "T__27", "T__28", "T__29", "T__30", "T__31", 
                  "T__32", "T__33", "T__34", "T__35", "T__36", "T__37", 
                  "T__38", "T__39", "T__40", "T__41", "T__42", "Uint", "MeKeyword", 
                  "AllKeyword", "VersionLiteral", "BooleanLiteral", "DecimalNumber", 
                  "ReservedKeyword", "AnonymousKeyword", "BreakKeyword", 
                  "ConstantKeyword", "ContinueKeyword", "ExternalKeyword", 
                  "IndexedKeyword", "InternalKeyword", "PayableKeyword", 
                  "PrivateKeyword", "PublicKeyword", "PureKeyword", "ViewKeyword", 
                  "FinalKeyword", "Identifier", "IdentifierStart", "IdentifierPart", 
                  "WS", "COMMENT", "LINE_COMMENT" ]

    grammarFileName = "Solidity.g4"

    def __init__(self, input=None, output:TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.7.2")
        self._interp = LexerATNSimulator(self, self.atn, self.decisionsToDFA, PredictionContextCache())
        self._actions = None
        self._predicates = None


