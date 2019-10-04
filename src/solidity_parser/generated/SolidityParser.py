# Generated from /home/nibau/msc-thesis/zkay/src/solidity_parser/Solidity.g4 by ANTLR 4.7.2
# encoding: utf-8
from antlr4 import *
from io import StringIO
from typing.io import TextIO
import sys


def serializedATN():
    with StringIO() as buf:
        buf.write("\3\u608b\ua72a\u8133\ub9ed\u417c\u3be7\u7786\u5964\3E")
        buf.write("\u0164\4\2\t\2\4\3\t\3\4\4\t\4\4\5\t\5\4\6\t\6\4\7\t\7")
        buf.write("\4\b\t\b\4\t\t\t\4\n\t\n\4\13\t\13\4\f\t\f\4\r\t\r\4\16")
        buf.write("\t\16\4\17\t\17\4\20\t\20\4\21\t\21\4\22\t\22\4\23\t\23")
        buf.write("\4\24\t\24\4\25\t\25\4\26\t\26\4\27\t\27\4\30\t\30\4\31")
        buf.write("\t\31\4\32\t\32\4\33\t\33\4\34\t\34\4\35\t\35\4\36\t\36")
        buf.write("\4\37\t\37\4 \t \4!\t!\4\"\t\"\4#\t#\4$\t$\4%\t%\4&\t")
        buf.write("&\3\2\3\2\7\2O\n\2\f\2\16\2R\13\2\3\2\3\2\3\3\3\3\3\3")
        buf.write("\3\3\3\3\3\4\3\4\3\5\3\5\5\5_\n\5\3\6\3\6\5\6c\n\6\3\7")
        buf.write("\3\7\3\b\5\bh\n\b\3\b\3\b\3\t\3\t\3\t\3\t\7\tp\n\t\f\t")
        buf.write("\16\ts\13\t\3\t\3\t\3\n\3\n\3\n\5\nz\n\n\3\13\7\13}\n")
        buf.write("\13\f\13\16\13\u0080\13\13\3\13\3\13\7\13\u0084\n\13\f")
        buf.write("\13\16\13\u0087\13\13\3\13\3\13\3\13\5\13\u008c\n\13\3")
        buf.write("\13\3\13\3\f\3\f\3\f\3\f\3\f\3\r\3\r\3\r\3\r\3\r\5\r\u009a")
        buf.write("\n\r\3\r\3\r\3\16\3\16\3\16\3\17\7\17\u00a2\n\17\f\17")
        buf.write("\16\17\u00a5\13\17\3\20\3\20\5\20\u00a9\n\20\3\21\3\21")
        buf.write("\3\21\3\21\7\21\u00af\n\21\f\21\16\21\u00b2\13\21\5\21")
        buf.write("\u00b4\n\21\3\21\3\21\3\22\5\22\u00b9\n\22\3\22\3\22\5")
        buf.write("\22\u00bd\n\22\3\23\5\23\u00c0\n\23\3\23\3\23\3\23\3\24")
        buf.write("\3\24\3\24\5\24\u00c8\n\24\3\25\3\25\3\26\3\26\3\26\3")
        buf.write("\26\3\26\5\26\u00d1\n\26\3\26\3\26\3\26\3\26\3\27\3\27")
        buf.write("\3\27\3\30\3\30\3\31\3\31\7\31\u00de\n\31\f\31\16\31\u00e1")
        buf.write("\13\31\3\31\3\31\3\32\3\32\3\32\3\32\3\32\5\32\u00ea\n")
        buf.write("\32\3\33\3\33\3\33\3\34\3\34\3\34\3\34\3\34\3\34\3\34")
        buf.write("\5\34\u00f6\n\34\3\35\3\35\3\35\3\35\3\35\3\35\3\36\3")
        buf.write("\36\5\36\u0100\n\36\3\37\3\37\5\37\u0104\n\37\3\37\3\37")
        buf.write("\3 \3 \3 \5 \u010b\n \3 \3 \3!\3!\3!\3!\3!\3!\3!\3!\3")
        buf.write("!\3!\3!\3!\3!\3!\5!\u011d\n!\3!\3!\3!\3!\3!\3!\3!\3!\3")
        buf.write("!\3!\3!\3!\3!\3!\3!\3!\3!\3!\3!\3!\3!\3!\3!\3!\3!\3!\3")
        buf.write("!\3!\3!\3!\3!\3!\3!\3!\3!\3!\3!\3!\3!\3!\3!\3!\3!\7!\u014a")
        buf.write("\n!\f!\16!\u014d\13!\3\"\3\"\3\"\7\"\u0152\n\"\f\"\16")
        buf.write("\"\u0155\13\"\5\"\u0157\n\"\3#\3#\3$\3$\3%\3%\3%\5%\u0160")
        buf.write("\n%\3&\3&\3&\2\3@\'\2\4\6\b\n\f\16\20\22\24\26\30\32\34")
        buf.write("\36 \"$&(*,.\60\62\64\668:<>@BDFHJ\2\b\3\2\5\13\4\2\25")
        buf.write("\26..\3\2!\"\3\2$&\3\2\7\n\3\2\'(\2\u0172\2L\3\2\2\2\4")
        buf.write("U\3\2\2\2\6Z\3\2\2\2\b^\3\2\2\2\n`\3\2\2\2\fd\3\2\2\2")
        buf.write("\16g\3\2\2\2\20k\3\2\2\2\22y\3\2\2\2\24~\3\2\2\2\26\u008f")
        buf.write("\3\2\2\2\30\u0094\3\2\2\2\32\u009d\3\2\2\2\34\u00a3\3")
        buf.write("\2\2\2\36\u00a8\3\2\2\2 \u00aa\3\2\2\2\"\u00b8\3\2\2\2")
        buf.write("$\u00bf\3\2\2\2&\u00c7\3\2\2\2(\u00c9\3\2\2\2*\u00cb\3")
        buf.write("\2\2\2,\u00d6\3\2\2\2.\u00d9\3\2\2\2\60\u00db\3\2\2\2")
        buf.write("\62\u00e9\3\2\2\2\64\u00eb\3\2\2\2\66\u00ee\3\2\2\28\u00f7")
        buf.write("\3\2\2\2:\u00ff\3\2\2\2<\u0101\3\2\2\2>\u0107\3\2\2\2")
        buf.write("@\u011c\3\2\2\2B\u0156\3\2\2\2D\u0158\3\2\2\2F\u015a\3")
        buf.write("\2\2\2H\u015c\3\2\2\2J\u0161\3\2\2\2LP\5\4\3\2MO\5\20")
        buf.write("\t\2NM\3\2\2\2OR\3\2\2\2PN\3\2\2\2PQ\3\2\2\2QS\3\2\2\2")
        buf.write("RP\3\2\2\2ST\7\2\2\3T\3\3\2\2\2UV\7\3\2\2VW\5\6\4\2WX")
        buf.write("\5\b\5\2XY\7\4\2\2Y\5\3\2\2\2Z[\5J&\2[\7\3\2\2\2\\_\5")
        buf.write("\n\6\2]_\5@!\2^\\\3\2\2\2^]\3\2\2\2_\t\3\2\2\2`b\5\16")
        buf.write("\b\2ac\5\16\b\2ba\3\2\2\2bc\3\2\2\2c\13\3\2\2\2de\t\2")
        buf.write("\2\2e\r\3\2\2\2fh\5\f\7\2gf\3\2\2\2gh\3\2\2\2hi\3\2\2")
        buf.write("\2ij\7\61\2\2j\17\3\2\2\2kl\7\f\2\2lm\5J&\2mq\7\r\2\2")
        buf.write("np\5\22\n\2on\3\2\2\2ps\3\2\2\2qo\3\2\2\2qr\3\2\2\2rt")
        buf.write("\3\2\2\2sq\3\2\2\2tu\7\16\2\2u\21\3\2\2\2vz\5\24\13\2")
        buf.write("wz\5\26\f\2xz\5\30\r\2yv\3\2\2\2yw\3\2\2\2yx\3\2\2\2z")
        buf.write("\23\3\2\2\2{}\7A\2\2|{\3\2\2\2}\u0080\3\2\2\2~|\3\2\2")
        buf.write("\2~\177\3\2\2\2\177\u0081\3\2\2\2\u0080~\3\2\2\2\u0081")
        buf.write("\u0085\5H%\2\u0082\u0084\7\67\2\2\u0083\u0082\3\2\2\2")
        buf.write("\u0084\u0087\3\2\2\2\u0085\u0083\3\2\2\2\u0085\u0086\3")
        buf.write("\2\2\2\u0086\u0088\3\2\2\2\u0087\u0085\3\2\2\2\u0088\u008b")
        buf.write("\5J&\2\u0089\u008a\7\13\2\2\u008a\u008c\5@!\2\u008b\u0089")
        buf.write("\3\2\2\2\u008b\u008c\3\2\2\2\u008c\u008d\3\2\2\2\u008d")
        buf.write("\u008e\7\4\2\2\u008e\25\3\2\2\2\u008f\u0090\7\17\2\2\u0090")
        buf.write("\u0091\5 \21\2\u0091\u0092\5\34\17\2\u0092\u0093\5\60")
        buf.write("\31\2\u0093\27\3\2\2\2\u0094\u0095\7\20\2\2\u0095\u0096")
        buf.write("\5J&\2\u0096\u0097\5 \21\2\u0097\u0099\5\34\17\2\u0098")
        buf.write("\u009a\5\32\16\2\u0099\u0098\3\2\2\2\u0099\u009a\3\2\2")
        buf.write("\2\u009a\u009b\3\2\2\2\u009b\u009c\5\60\31\2\u009c\31")
        buf.write("\3\2\2\2\u009d\u009e\7\21\2\2\u009e\u009f\5 \21\2\u009f")
        buf.write("\33\3\2\2\2\u00a0\u00a2\5\36\20\2\u00a1\u00a0\3\2\2\2")
        buf.write("\u00a2\u00a5\3\2\2\2\u00a3\u00a1\3\2\2\2\u00a3\u00a4\3")
        buf.write("\2\2\2\u00a4\35\3\2\2\2\u00a5\u00a3\3\2\2\2\u00a6\u00a9")
        buf.write("\5.\30\2\u00a7\u00a9\7>\2\2\u00a8\u00a6\3\2\2\2\u00a8")
        buf.write("\u00a7\3\2\2\2\u00a9\37\3\2\2\2\u00aa\u00b3\7\22\2\2\u00ab")
        buf.write("\u00b0\5\"\22\2\u00ac\u00ad\7\23\2\2\u00ad\u00af\5\"\22")
        buf.write("\2\u00ae\u00ac\3\2\2\2\u00af\u00b2\3\2\2\2\u00b0\u00ae")
        buf.write("\3\2\2\2\u00b0\u00b1\3\2\2\2\u00b1\u00b4\3\2\2\2\u00b2")
        buf.write("\u00b0\3\2\2\2\u00b3\u00ab\3\2\2\2\u00b3\u00b4\3\2\2\2")
        buf.write("\u00b4\u00b5\3\2\2\2\u00b5\u00b6\7\24\2\2\u00b6!\3\2\2")
        buf.write("\2\u00b7\u00b9\7A\2\2\u00b8\u00b7\3\2\2\2\u00b8\u00b9")
        buf.write("\3\2\2\2\u00b9\u00ba\3\2\2\2\u00ba\u00bc\5H%\2\u00bb\u00bd")
        buf.write("\5J&\2\u00bc\u00bb\3\2\2\2\u00bc\u00bd\3\2\2\2\u00bd#")
        buf.write("\3\2\2\2\u00be\u00c0\7A\2\2\u00bf\u00be\3\2\2\2\u00bf")
        buf.write("\u00c0\3\2\2\2\u00c0\u00c1\3\2\2\2\u00c1\u00c2\5H%\2\u00c2")
        buf.write("\u00c3\5J&\2\u00c3%\3\2\2\2\u00c4\u00c8\5(\25\2\u00c5")
        buf.write("\u00c8\5*\26\2\u00c6\u00c8\5,\27\2\u00c7\u00c4\3\2\2\2")
        buf.write("\u00c7\u00c5\3\2\2\2\u00c7\u00c6\3\2\2\2\u00c8\'\3\2\2")
        buf.write("\2\u00c9\u00ca\t\3\2\2\u00ca)\3\2\2\2\u00cb\u00cc\7\27")
        buf.write("\2\2\u00cc\u00cd\7\22\2\2\u00cd\u00d0\5(\25\2\u00ce\u00cf")
        buf.write("\7\30\2\2\u00cf\u00d1\5J&\2\u00d0\u00ce\3\2\2\2\u00d0")
        buf.write("\u00d1\3\2\2\2\u00d1\u00d2\3\2\2\2\u00d2\u00d3\7\31\2")
        buf.write("\2\u00d3\u00d4\5H%\2\u00d4\u00d5\7\24\2\2\u00d5+\3\2\2")
        buf.write("\2\u00d6\u00d7\7\25\2\2\u00d7\u00d8\7<\2\2\u00d8-\3\2")
        buf.write("\2\2\u00d9\u00da\7<\2\2\u00da/\3\2\2\2\u00db\u00df\7\r")
        buf.write("\2\2\u00dc\u00de\5\62\32\2\u00dd\u00dc\3\2\2\2\u00de\u00e1")
        buf.write("\3\2\2\2\u00df\u00dd\3\2\2\2\u00df\u00e0\3\2\2\2\u00e0")
        buf.write("\u00e2\3\2\2\2\u00e1\u00df\3\2\2\2\u00e2\u00e3\7\16\2")
        buf.write("\2\u00e3\61\3\2\2\2\u00e4\u00ea\5\66\34\2\u00e5\u00ea")
        buf.write("\58\35\2\u00e6\u00ea\5\60\31\2\u00e7\u00ea\5<\37\2\u00e8")
        buf.write("\u00ea\5:\36\2\u00e9\u00e4\3\2\2\2\u00e9\u00e5\3\2\2\2")
        buf.write("\u00e9\u00e6\3\2\2\2\u00e9\u00e7\3\2\2\2\u00e9\u00e8\3")
        buf.write("\2\2\2\u00ea\63\3\2\2\2\u00eb\u00ec\5@!\2\u00ec\u00ed")
        buf.write("\7\4\2\2\u00ed\65\3\2\2\2\u00ee\u00ef\7\32\2\2\u00ef\u00f0")
        buf.write("\7\22\2\2\u00f0\u00f1\5@!\2\u00f1\u00f2\7\24\2\2\u00f2")
        buf.write("\u00f5\5\62\32\2\u00f3\u00f4\7\33\2\2\u00f4\u00f6\5\62")
        buf.write("\32\2\u00f5\u00f3\3\2\2\2\u00f5\u00f6\3\2\2\2\u00f6\67")
        buf.write("\3\2\2\2\u00f7\u00f8\7\34\2\2\u00f8\u00f9\7\22\2\2\u00f9")
        buf.write("\u00fa\5@!\2\u00fa\u00fb\7\24\2\2\u00fb\u00fc\5\62\32")
        buf.write("\2\u00fc9\3\2\2\2\u00fd\u0100\5> \2\u00fe\u0100\5\64\33")
        buf.write("\2\u00ff\u00fd\3\2\2\2\u00ff\u00fe\3\2\2\2\u0100;\3\2")
        buf.write("\2\2\u0101\u0103\7\35\2\2\u0102\u0104\5@!\2\u0103\u0102")
        buf.write("\3\2\2\2\u0103\u0104\3\2\2\2\u0104\u0105\3\2\2\2\u0105")
        buf.write("\u0106\7\4\2\2\u0106=\3\2\2\2\u0107\u010a\5$\23\2\u0108")
        buf.write("\u0109\7\13\2\2\u0109\u010b\5@!\2\u010a\u0108\3\2\2\2")
        buf.write("\u010a\u010b\3\2\2\2\u010b\u010c\3\2\2\2\u010c\u010d\7")
        buf.write("\4\2\2\u010d?\3\2\2\2\u010e\u010f\b!\1\2\u010f\u011d\7")
        buf.write("/\2\2\u0110\u011d\7\60\2\2\u0111\u0112\7\22\2\2\u0112")
        buf.write("\u0113\5@!\2\u0113\u0114\7\24\2\2\u0114\u011d\3\2\2\2")
        buf.write("\u0115\u0116\t\4\2\2\u0116\u011d\5@!\20\u0117\u0118\7")
        buf.write("\30\2\2\u0118\u011d\5@!\17\u0119\u011d\7\62\2\2\u011a")
        buf.write("\u011d\5F$\2\u011b\u011d\5J&\2\u011c\u010e\3\2\2\2\u011c")
        buf.write("\u0110\3\2\2\2\u011c\u0111\3\2\2\2\u011c\u0115\3\2\2\2")
        buf.write("\u011c\u0117\3\2\2\2\u011c\u0119\3\2\2\2\u011c\u011a\3")
        buf.write("\2\2\2\u011c\u011b\3\2\2\2\u011d\u014b\3\2\2\2\u011e\u011f")
        buf.write("\f\16\2\2\u011f\u0120\7#\2\2\u0120\u014a\5@!\17\u0121")
        buf.write("\u0122\f\r\2\2\u0122\u0123\t\5\2\2\u0123\u014a\5@!\16")
        buf.write("\u0124\u0125\f\f\2\2\u0125\u0126\t\4\2\2\u0126\u014a\5")
        buf.write("@!\r\u0127\u0128\f\13\2\2\u0128\u0129\t\6\2\2\u0129\u014a")
        buf.write("\5@!\f\u012a\u012b\f\n\2\2\u012b\u012c\t\7\2\2\u012c\u014a")
        buf.write("\5@!\13\u012d\u012e\f\t\2\2\u012e\u012f\7)\2\2\u012f\u014a")
        buf.write("\5@!\n\u0130\u0131\f\b\2\2\u0131\u0132\7*\2\2\u0132\u014a")
        buf.write("\5@!\t\u0133\u0134\f\7\2\2\u0134\u0135\7+\2\2\u0135\u0136")
        buf.write("\5@!\2\u0136\u0137\7,\2\2\u0137\u0138\5@!\b\u0138\u014a")
        buf.write("\3\2\2\2\u0139\u013a\f\6\2\2\u013a\u013b\7\13\2\2\u013b")
        buf.write("\u014a\5@!\7\u013c\u013d\f\24\2\2\u013d\u013e\7\36\2\2")
        buf.write("\u013e\u013f\5@!\2\u013f\u0140\7\37\2\2\u0140\u014a\3")
        buf.write("\2\2\2\u0141\u0142\f\23\2\2\u0142\u0143\7\22\2\2\u0143")
        buf.write("\u0144\5B\"\2\u0144\u0145\7\24\2\2\u0145\u014a\3\2\2\2")
        buf.write("\u0146\u0147\f\22\2\2\u0147\u0148\7 \2\2\u0148\u014a\5")
        buf.write("J&\2\u0149\u011e\3\2\2\2\u0149\u0121\3\2\2\2\u0149\u0124")
        buf.write("\3\2\2\2\u0149\u0127\3\2\2\2\u0149\u012a\3\2\2\2\u0149")
        buf.write("\u012d\3\2\2\2\u0149\u0130\3\2\2\2\u0149\u0133\3\2\2\2")
        buf.write("\u0149\u0139\3\2\2\2\u0149\u013c\3\2\2\2\u0149\u0141\3")
        buf.write("\2\2\2\u0149\u0146\3\2\2\2\u014a\u014d\3\2\2\2\u014b\u0149")
        buf.write("\3\2\2\2\u014b\u014c\3\2\2\2\u014cA\3\2\2\2\u014d\u014b")
        buf.write("\3\2\2\2\u014e\u0153\5@!\2\u014f\u0150\7\23\2\2\u0150")
        buf.write("\u0152\5@!\2\u0151\u014f\3\2\2\2\u0152\u0155\3\2\2\2\u0153")
        buf.write("\u0151\3\2\2\2\u0153\u0154\3\2\2\2\u0154\u0157\3\2\2\2")
        buf.write("\u0155\u0153\3\2\2\2\u0156\u014e\3\2\2\2\u0156\u0157\3")
        buf.write("\2\2\2\u0157C\3\2\2\2\u0158\u0159\5(\25\2\u0159E\3\2\2")
        buf.write("\2\u015a\u015b\7\63\2\2\u015bG\3\2\2\2\u015c\u015f\5&")
        buf.write("\24\2\u015d\u015e\7-\2\2\u015e\u0160\5@!\2\u015f\u015d")
        buf.write("\3\2\2\2\u015f\u0160\3\2\2\2\u0160I\3\2\2\2\u0161\u0162")
        buf.write("\7B\2\2\u0162K\3\2\2\2!P^bgqy~\u0085\u008b\u0099\u00a3")
        buf.write("\u00a8\u00b0\u00b3\u00b8\u00bc\u00bf\u00c7\u00d0\u00df")
        buf.write("\u00e9\u00f5\u00ff\u0103\u010a\u011c\u0149\u014b\u0153")
        buf.write("\u0156\u015f")
        return buf.getvalue()


class SolidityParser ( Parser ):

    grammarFileName = "Solidity.g4"

    atn = ATNDeserializer().deserialize(serializedATN())

    decisionsToDFA = [ DFA(ds, i) for i, ds in enumerate(atn.decisionToState) ]

    sharedContextCache = PredictionContextCache()

    literalNames = [ "<INVALID>", "'pragma'", "';'", "'^'", "'~'", "'>='", 
                     "'>'", "'<'", "'<='", "'='", "'contract'", "'{'", "'}'", 
                     "'constructor'", "'function'", "'returns'", "'('", 
                     "','", "')'", "'address'", "'bool'", "'mapping'", "'!'", 
                     "'=>'", "'if'", "'else'", "'while'", "'return'", "'['", 
                     "']'", "'.'", "'+'", "'-'", "'**'", "'*'", "'/'", "'%'", 
                     "'=='", "'!='", "'&&'", "'||'", "'?'", "':'", "'@'", 
                     "'uint'", "'me'", "'all'", "<INVALID>", "<INVALID>", 
                     "<INVALID>", "<INVALID>", "'anonymous'", "'break'", 
                     "'constant'", "'continue'", "'external'", "'indexed'", 
                     "'internal'", "'payable'", "'private'", "'public'", 
                     "'pure'", "'view'", "'final'" ]

    symbolicNames = [ "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "<INVALID>", "<INVALID>", "<INVALID>", "<INVALID>", 
                      "Uint", "MeKeyword", "AllKeyword", "VersionLiteral", 
                      "BooleanLiteral", "DecimalNumber", "ReservedKeyword", 
                      "AnonymousKeyword", "BreakKeyword", "ConstantKeyword", 
                      "ContinueKeyword", "ExternalKeyword", "IndexedKeyword", 
                      "InternalKeyword", "PayableKeyword", "PrivateKeyword", 
                      "PublicKeyword", "PureKeyword", "ViewKeyword", "FinalKeyword", 
                      "Identifier", "WS", "COMMENT", "LINE_COMMENT" ]

    RULE_sourceUnit = 0
    RULE_pragmaDirective = 1
    RULE_pragmaName = 2
    RULE_pragmaValue = 3
    RULE_version = 4
    RULE_versionOperator = 5
    RULE_versionConstraint = 6
    RULE_contractDefinition = 7
    RULE_contractPart = 8
    RULE_stateVariableDeclaration = 9
    RULE_constructorDefinition = 10
    RULE_functionDefinition = 11
    RULE_returnParameters = 12
    RULE_modifierList = 13
    RULE_modifier = 14
    RULE_parameterList = 15
    RULE_parameter = 16
    RULE_variableDeclaration = 17
    RULE_typeName = 18
    RULE_elementaryTypeName = 19
    RULE_mapping = 20
    RULE_payableAddress = 21
    RULE_stateMutability = 22
    RULE_block = 23
    RULE_statement = 24
    RULE_expressionStatement = 25
    RULE_ifStatement = 26
    RULE_whileStatement = 27
    RULE_simpleStatement = 28
    RULE_returnStatement = 29
    RULE_variableDeclarationStatement = 30
    RULE_expression = 31
    RULE_functionCallArguments = 32
    RULE_elementaryTypeNameExpression = 33
    RULE_numberLiteral = 34
    RULE_annotatedTypeName = 35
    RULE_identifier = 36

    ruleNames =  [ "sourceUnit", "pragmaDirective", "pragmaName", "pragmaValue", 
                   "version", "versionOperator", "versionConstraint", "contractDefinition", 
                   "contractPart", "stateVariableDeclaration", "constructorDefinition", 
                   "functionDefinition", "returnParameters", "modifierList", 
                   "modifier", "parameterList", "parameter", "variableDeclaration", 
                   "typeName", "elementaryTypeName", "mapping", "payableAddress", 
                   "stateMutability", "block", "statement", "expressionStatement", 
                   "ifStatement", "whileStatement", "simpleStatement", "returnStatement", 
                   "variableDeclarationStatement", "expression", "functionCallArguments", 
                   "elementaryTypeNameExpression", "numberLiteral", "annotatedTypeName", 
                   "identifier" ]

    EOF = Token.EOF
    T__0=1
    T__1=2
    T__2=3
    T__3=4
    T__4=5
    T__5=6
    T__6=7
    T__7=8
    T__8=9
    T__9=10
    T__10=11
    T__11=12
    T__12=13
    T__13=14
    T__14=15
    T__15=16
    T__16=17
    T__17=18
    T__18=19
    T__19=20
    T__20=21
    T__21=22
    T__22=23
    T__23=24
    T__24=25
    T__25=26
    T__26=27
    T__27=28
    T__28=29
    T__29=30
    T__30=31
    T__31=32
    T__32=33
    T__33=34
    T__34=35
    T__35=36
    T__36=37
    T__37=38
    T__38=39
    T__39=40
    T__40=41
    T__41=42
    T__42=43
    Uint=44
    MeKeyword=45
    AllKeyword=46
    VersionLiteral=47
    BooleanLiteral=48
    DecimalNumber=49
    ReservedKeyword=50
    AnonymousKeyword=51
    BreakKeyword=52
    ConstantKeyword=53
    ContinueKeyword=54
    ExternalKeyword=55
    IndexedKeyword=56
    InternalKeyword=57
    PayableKeyword=58
    PrivateKeyword=59
    PublicKeyword=60
    PureKeyword=61
    ViewKeyword=62
    FinalKeyword=63
    Identifier=64
    WS=65
    COMMENT=66
    LINE_COMMENT=67

    def __init__(self, input:TokenStream, output:TextIO = sys.stdout):
        super().__init__(input, output)
        self.checkVersion("4.7.2")
        self._interp = ParserATNSimulator(self, self.atn, self.decisionsToDFA, self.sharedContextCache)
        self._predicates = None




    class SourceUnitContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser
            self.pragma_directive = None # PragmaDirectiveContext
            self._contractDefinition = None # ContractDefinitionContext
            self.contracts = list() # of ContractDefinitionContexts

        def EOF(self):
            return self.getToken(SolidityParser.EOF, 0)

        def pragmaDirective(self):
            return self.getTypedRuleContext(SolidityParser.PragmaDirectiveContext,0)


        def contractDefinition(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(SolidityParser.ContractDefinitionContext)
            else:
                return self.getTypedRuleContext(SolidityParser.ContractDefinitionContext,i)


        def getRuleIndex(self):
            return SolidityParser.RULE_sourceUnit

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterSourceUnit" ):
                listener.enterSourceUnit(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitSourceUnit" ):
                listener.exitSourceUnit(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitSourceUnit" ):
                return visitor.visitSourceUnit(self)
            else:
                return visitor.visitChildren(self)




    def sourceUnit(self):

        localctx = SolidityParser.SourceUnitContext(self, self._ctx, self.state)
        self.enterRule(localctx, 0, self.RULE_sourceUnit)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 74
            localctx.pragma_directive = self.pragmaDirective()
            self.state = 78
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==SolidityParser.T__9:
                self.state = 75
                localctx._contractDefinition = self.contractDefinition()
                localctx.contracts.append(localctx._contractDefinition)
                self.state = 80
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 81
            self.match(SolidityParser.EOF)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class PragmaDirectiveContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def pragmaName(self):
            return self.getTypedRuleContext(SolidityParser.PragmaNameContext,0)


        def pragmaValue(self):
            return self.getTypedRuleContext(SolidityParser.PragmaValueContext,0)


        def getRuleIndex(self):
            return SolidityParser.RULE_pragmaDirective

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterPragmaDirective" ):
                listener.enterPragmaDirective(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitPragmaDirective" ):
                listener.exitPragmaDirective(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitPragmaDirective" ):
                return visitor.visitPragmaDirective(self)
            else:
                return visitor.visitChildren(self)




    def pragmaDirective(self):

        localctx = SolidityParser.PragmaDirectiveContext(self, self._ctx, self.state)
        self.enterRule(localctx, 2, self.RULE_pragmaDirective)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 83
            self.match(SolidityParser.T__0)
            self.state = 84
            self.pragmaName()
            self.state = 85
            self.pragmaValue()
            self.state = 86
            self.match(SolidityParser.T__1)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class PragmaNameContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def identifier(self):
            return self.getTypedRuleContext(SolidityParser.IdentifierContext,0)


        def getRuleIndex(self):
            return SolidityParser.RULE_pragmaName

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterPragmaName" ):
                listener.enterPragmaName(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitPragmaName" ):
                listener.exitPragmaName(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitPragmaName" ):
                return visitor.visitPragmaName(self)
            else:
                return visitor.visitChildren(self)




    def pragmaName(self):

        localctx = SolidityParser.PragmaNameContext(self, self._ctx, self.state)
        self.enterRule(localctx, 4, self.RULE_pragmaName)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 88
            self.identifier()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class PragmaValueContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def version(self):
            return self.getTypedRuleContext(SolidityParser.VersionContext,0)


        def expression(self):
            return self.getTypedRuleContext(SolidityParser.ExpressionContext,0)


        def getRuleIndex(self):
            return SolidityParser.RULE_pragmaValue

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterPragmaValue" ):
                listener.enterPragmaValue(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitPragmaValue" ):
                listener.exitPragmaValue(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitPragmaValue" ):
                return visitor.visitPragmaValue(self)
            else:
                return visitor.visitChildren(self)




    def pragmaValue(self):

        localctx = SolidityParser.PragmaValueContext(self, self._ctx, self.state)
        self.enterRule(localctx, 6, self.RULE_pragmaValue)
        try:
            self.state = 92
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [SolidityParser.T__2, SolidityParser.T__3, SolidityParser.T__4, SolidityParser.T__5, SolidityParser.T__6, SolidityParser.T__7, SolidityParser.T__8, SolidityParser.VersionLiteral]:
                self.enterOuterAlt(localctx, 1)
                self.state = 90
                self.version()
                pass
            elif token in [SolidityParser.T__15, SolidityParser.T__21, SolidityParser.T__30, SolidityParser.T__31, SolidityParser.MeKeyword, SolidityParser.AllKeyword, SolidityParser.BooleanLiteral, SolidityParser.DecimalNumber, SolidityParser.Identifier]:
                self.enterOuterAlt(localctx, 2)
                self.state = 91
                self.expression(0)
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class VersionContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def versionConstraint(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(SolidityParser.VersionConstraintContext)
            else:
                return self.getTypedRuleContext(SolidityParser.VersionConstraintContext,i)


        def getRuleIndex(self):
            return SolidityParser.RULE_version

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterVersion" ):
                listener.enterVersion(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitVersion" ):
                listener.exitVersion(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitVersion" ):
                return visitor.visitVersion(self)
            else:
                return visitor.visitChildren(self)




    def version(self):

        localctx = SolidityParser.VersionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 8, self.RULE_version)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 94
            self.versionConstraint()
            self.state = 96
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if (((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << SolidityParser.T__2) | (1 << SolidityParser.T__3) | (1 << SolidityParser.T__4) | (1 << SolidityParser.T__5) | (1 << SolidityParser.T__6) | (1 << SolidityParser.T__7) | (1 << SolidityParser.T__8) | (1 << SolidityParser.VersionLiteral))) != 0):
                self.state = 95
                self.versionConstraint()


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class VersionOperatorContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return SolidityParser.RULE_versionOperator

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterVersionOperator" ):
                listener.enterVersionOperator(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitVersionOperator" ):
                listener.exitVersionOperator(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitVersionOperator" ):
                return visitor.visitVersionOperator(self)
            else:
                return visitor.visitChildren(self)




    def versionOperator(self):

        localctx = SolidityParser.VersionOperatorContext(self, self._ctx, self.state)
        self.enterRule(localctx, 10, self.RULE_versionOperator)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 98
            _la = self._input.LA(1)
            if not((((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << SolidityParser.T__2) | (1 << SolidityParser.T__3) | (1 << SolidityParser.T__4) | (1 << SolidityParser.T__5) | (1 << SolidityParser.T__6) | (1 << SolidityParser.T__7) | (1 << SolidityParser.T__8))) != 0)):
                self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class VersionConstraintContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def VersionLiteral(self):
            return self.getToken(SolidityParser.VersionLiteral, 0)

        def versionOperator(self):
            return self.getTypedRuleContext(SolidityParser.VersionOperatorContext,0)


        def getRuleIndex(self):
            return SolidityParser.RULE_versionConstraint

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterVersionConstraint" ):
                listener.enterVersionConstraint(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitVersionConstraint" ):
                listener.exitVersionConstraint(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitVersionConstraint" ):
                return visitor.visitVersionConstraint(self)
            else:
                return visitor.visitChildren(self)




    def versionConstraint(self):

        localctx = SolidityParser.VersionConstraintContext(self, self._ctx, self.state)
        self.enterRule(localctx, 12, self.RULE_versionConstraint)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 101
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if (((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << SolidityParser.T__2) | (1 << SolidityParser.T__3) | (1 << SolidityParser.T__4) | (1 << SolidityParser.T__5) | (1 << SolidityParser.T__6) | (1 << SolidityParser.T__7) | (1 << SolidityParser.T__8))) != 0):
                self.state = 100
                self.versionOperator()


            self.state = 103
            self.match(SolidityParser.VersionLiteral)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ContractDefinitionContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser
            self._contractPart = None # ContractPartContext
            self.parts = list() # of ContractPartContexts

        def identifier(self):
            return self.getTypedRuleContext(SolidityParser.IdentifierContext,0)


        def contractPart(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(SolidityParser.ContractPartContext)
            else:
                return self.getTypedRuleContext(SolidityParser.ContractPartContext,i)


        def getRuleIndex(self):
            return SolidityParser.RULE_contractDefinition

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterContractDefinition" ):
                listener.enterContractDefinition(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitContractDefinition" ):
                listener.exitContractDefinition(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitContractDefinition" ):
                return visitor.visitContractDefinition(self)
            else:
                return visitor.visitChildren(self)




    def contractDefinition(self):

        localctx = SolidityParser.ContractDefinitionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 14, self.RULE_contractDefinition)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 105
            self.match(SolidityParser.T__9)
            self.state = 106
            self.identifier()
            self.state = 107
            self.match(SolidityParser.T__10)
            self.state = 111
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while (((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << SolidityParser.T__12) | (1 << SolidityParser.T__13) | (1 << SolidityParser.T__18) | (1 << SolidityParser.T__19) | (1 << SolidityParser.T__20) | (1 << SolidityParser.Uint) | (1 << SolidityParser.FinalKeyword))) != 0):
                self.state = 108
                localctx._contractPart = self.contractPart()
                localctx.parts.append(localctx._contractPart)
                self.state = 113
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 114
            self.match(SolidityParser.T__11)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ContractPartContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def stateVariableDeclaration(self):
            return self.getTypedRuleContext(SolidityParser.StateVariableDeclarationContext,0)


        def constructorDefinition(self):
            return self.getTypedRuleContext(SolidityParser.ConstructorDefinitionContext,0)


        def functionDefinition(self):
            return self.getTypedRuleContext(SolidityParser.FunctionDefinitionContext,0)


        def getRuleIndex(self):
            return SolidityParser.RULE_contractPart

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterContractPart" ):
                listener.enterContractPart(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitContractPart" ):
                listener.exitContractPart(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitContractPart" ):
                return visitor.visitContractPart(self)
            else:
                return visitor.visitChildren(self)




    def contractPart(self):

        localctx = SolidityParser.ContractPartContext(self, self._ctx, self.state)
        self.enterRule(localctx, 16, self.RULE_contractPart)
        try:
            self.state = 119
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [SolidityParser.T__18, SolidityParser.T__19, SolidityParser.T__20, SolidityParser.Uint, SolidityParser.FinalKeyword]:
                self.enterOuterAlt(localctx, 1)
                self.state = 116
                self.stateVariableDeclaration()
                pass
            elif token in [SolidityParser.T__12]:
                self.enterOuterAlt(localctx, 2)
                self.state = 117
                self.constructorDefinition()
                pass
            elif token in [SolidityParser.T__13]:
                self.enterOuterAlt(localctx, 3)
                self.state = 118
                self.functionDefinition()
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class StateVariableDeclarationContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser
            self._FinalKeyword = None # Token
            self.keywords = list() # of Tokens
            self.annotated_type = None # AnnotatedTypeNameContext
            self._ConstantKeyword = None # Token
            self.idf = None # IdentifierContext
            self.expr = None # ExpressionContext

        def annotatedTypeName(self):
            return self.getTypedRuleContext(SolidityParser.AnnotatedTypeNameContext,0)


        def identifier(self):
            return self.getTypedRuleContext(SolidityParser.IdentifierContext,0)


        def FinalKeyword(self, i:int=None):
            if i is None:
                return self.getTokens(SolidityParser.FinalKeyword)
            else:
                return self.getToken(SolidityParser.FinalKeyword, i)

        def ConstantKeyword(self, i:int=None):
            if i is None:
                return self.getTokens(SolidityParser.ConstantKeyword)
            else:
                return self.getToken(SolidityParser.ConstantKeyword, i)

        def expression(self):
            return self.getTypedRuleContext(SolidityParser.ExpressionContext,0)


        def getRuleIndex(self):
            return SolidityParser.RULE_stateVariableDeclaration

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterStateVariableDeclaration" ):
                listener.enterStateVariableDeclaration(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitStateVariableDeclaration" ):
                listener.exitStateVariableDeclaration(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitStateVariableDeclaration" ):
                return visitor.visitStateVariableDeclaration(self)
            else:
                return visitor.visitChildren(self)




    def stateVariableDeclaration(self):

        localctx = SolidityParser.StateVariableDeclarationContext(self, self._ctx, self.state)
        self.enterRule(localctx, 18, self.RULE_stateVariableDeclaration)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 124
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==SolidityParser.FinalKeyword:
                self.state = 121
                localctx._FinalKeyword = self.match(SolidityParser.FinalKeyword)
                localctx.keywords.append(localctx._FinalKeyword)
                self.state = 126
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 127
            localctx.annotated_type = self.annotatedTypeName()
            self.state = 131
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==SolidityParser.ConstantKeyword:
                self.state = 128
                localctx._ConstantKeyword = self.match(SolidityParser.ConstantKeyword)
                localctx.keywords.append(localctx._ConstantKeyword)
                self.state = 133
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 134
            localctx.idf = self.identifier()
            self.state = 137
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==SolidityParser.T__8:
                self.state = 135
                self.match(SolidityParser.T__8)
                self.state = 136
                localctx.expr = self.expression(0)


            self.state = 139
            self.match(SolidityParser.T__1)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ConstructorDefinitionContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser
            self.parameters = None # ParameterListContext
            self.modifiers = None # ModifierListContext
            self.body = None # BlockContext

        def parameterList(self):
            return self.getTypedRuleContext(SolidityParser.ParameterListContext,0)


        def modifierList(self):
            return self.getTypedRuleContext(SolidityParser.ModifierListContext,0)


        def block(self):
            return self.getTypedRuleContext(SolidityParser.BlockContext,0)


        def getRuleIndex(self):
            return SolidityParser.RULE_constructorDefinition

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterConstructorDefinition" ):
                listener.enterConstructorDefinition(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitConstructorDefinition" ):
                listener.exitConstructorDefinition(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitConstructorDefinition" ):
                return visitor.visitConstructorDefinition(self)
            else:
                return visitor.visitChildren(self)




    def constructorDefinition(self):

        localctx = SolidityParser.ConstructorDefinitionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 20, self.RULE_constructorDefinition)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 141
            self.match(SolidityParser.T__12)
            self.state = 142
            localctx.parameters = self.parameterList()
            self.state = 143
            localctx.modifiers = self.modifierList()
            self.state = 144
            localctx.body = self.block()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class FunctionDefinitionContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser
            self.idf = None # IdentifierContext
            self.parameters = None # ParameterListContext
            self.modifiers = None # ModifierListContext
            self.return_parameters = None # ReturnParametersContext
            self.body = None # BlockContext

        def identifier(self):
            return self.getTypedRuleContext(SolidityParser.IdentifierContext,0)


        def parameterList(self):
            return self.getTypedRuleContext(SolidityParser.ParameterListContext,0)


        def modifierList(self):
            return self.getTypedRuleContext(SolidityParser.ModifierListContext,0)


        def block(self):
            return self.getTypedRuleContext(SolidityParser.BlockContext,0)


        def returnParameters(self):
            return self.getTypedRuleContext(SolidityParser.ReturnParametersContext,0)


        def getRuleIndex(self):
            return SolidityParser.RULE_functionDefinition

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterFunctionDefinition" ):
                listener.enterFunctionDefinition(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitFunctionDefinition" ):
                listener.exitFunctionDefinition(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitFunctionDefinition" ):
                return visitor.visitFunctionDefinition(self)
            else:
                return visitor.visitChildren(self)




    def functionDefinition(self):

        localctx = SolidityParser.FunctionDefinitionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 22, self.RULE_functionDefinition)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 146
            self.match(SolidityParser.T__13)
            self.state = 147
            localctx.idf = self.identifier()
            self.state = 148
            localctx.parameters = self.parameterList()
            self.state = 149
            localctx.modifiers = self.modifierList()
            self.state = 151
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==SolidityParser.T__14:
                self.state = 150
                localctx.return_parameters = self.returnParameters()


            self.state = 153
            localctx.body = self.block()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ReturnParametersContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser
            self.return_parameters = None # ParameterListContext

        def parameterList(self):
            return self.getTypedRuleContext(SolidityParser.ParameterListContext,0)


        def getRuleIndex(self):
            return SolidityParser.RULE_returnParameters

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterReturnParameters" ):
                listener.enterReturnParameters(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitReturnParameters" ):
                listener.exitReturnParameters(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitReturnParameters" ):
                return visitor.visitReturnParameters(self)
            else:
                return visitor.visitChildren(self)




    def returnParameters(self):

        localctx = SolidityParser.ReturnParametersContext(self, self._ctx, self.state)
        self.enterRule(localctx, 24, self.RULE_returnParameters)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 155
            self.match(SolidityParser.T__14)
            self.state = 156
            localctx.return_parameters = self.parameterList()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ModifierListContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser
            self._modifier = None # ModifierContext
            self.modifiers = list() # of ModifierContexts

        def modifier(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(SolidityParser.ModifierContext)
            else:
                return self.getTypedRuleContext(SolidityParser.ModifierContext,i)


        def getRuleIndex(self):
            return SolidityParser.RULE_modifierList

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterModifierList" ):
                listener.enterModifierList(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitModifierList" ):
                listener.exitModifierList(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitModifierList" ):
                return visitor.visitModifierList(self)
            else:
                return visitor.visitChildren(self)




    def modifierList(self):

        localctx = SolidityParser.ModifierListContext(self, self._ctx, self.state)
        self.enterRule(localctx, 26, self.RULE_modifierList)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 161
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while _la==SolidityParser.PayableKeyword or _la==SolidityParser.PublicKeyword:
                self.state = 158
                localctx._modifier = self.modifier()
                localctx.modifiers.append(localctx._modifier)
                self.state = 163
                self._errHandler.sync(self)
                _la = self._input.LA(1)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ModifierContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def stateMutability(self):
            return self.getTypedRuleContext(SolidityParser.StateMutabilityContext,0)


        def PublicKeyword(self):
            return self.getToken(SolidityParser.PublicKeyword, 0)

        def getRuleIndex(self):
            return SolidityParser.RULE_modifier

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterModifier" ):
                listener.enterModifier(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitModifier" ):
                listener.exitModifier(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitModifier" ):
                return visitor.visitModifier(self)
            else:
                return visitor.visitChildren(self)




    def modifier(self):

        localctx = SolidityParser.ModifierContext(self, self._ctx, self.state)
        self.enterRule(localctx, 28, self.RULE_modifier)
        try:
            self.state = 166
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [SolidityParser.PayableKeyword]:
                self.enterOuterAlt(localctx, 1)
                self.state = 164
                self.stateMutability()
                pass
            elif token in [SolidityParser.PublicKeyword]:
                self.enterOuterAlt(localctx, 2)
                self.state = 165
                self.match(SolidityParser.PublicKeyword)
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ParameterListContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser
            self._parameter = None # ParameterContext
            self.params = list() # of ParameterContexts

        def parameter(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(SolidityParser.ParameterContext)
            else:
                return self.getTypedRuleContext(SolidityParser.ParameterContext,i)


        def getRuleIndex(self):
            return SolidityParser.RULE_parameterList

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterParameterList" ):
                listener.enterParameterList(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitParameterList" ):
                listener.exitParameterList(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitParameterList" ):
                return visitor.visitParameterList(self)
            else:
                return visitor.visitChildren(self)




    def parameterList(self):

        localctx = SolidityParser.ParameterListContext(self, self._ctx, self.state)
        self.enterRule(localctx, 30, self.RULE_parameterList)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 168
            self.match(SolidityParser.T__15)
            self.state = 177
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if (((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << SolidityParser.T__18) | (1 << SolidityParser.T__19) | (1 << SolidityParser.T__20) | (1 << SolidityParser.Uint) | (1 << SolidityParser.FinalKeyword))) != 0):
                self.state = 169
                localctx._parameter = self.parameter()
                localctx.params.append(localctx._parameter)
                self.state = 174
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                while _la==SolidityParser.T__16:
                    self.state = 170
                    self.match(SolidityParser.T__16)
                    self.state = 171
                    localctx._parameter = self.parameter()
                    localctx.params.append(localctx._parameter)
                    self.state = 176
                    self._errHandler.sync(self)
                    _la = self._input.LA(1)



            self.state = 179
            self.match(SolidityParser.T__17)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ParameterContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser
            self._FinalKeyword = None # Token
            self.keywords = list() # of Tokens
            self.annotated_type = None # AnnotatedTypeNameContext
            self.idf = None # IdentifierContext

        def annotatedTypeName(self):
            return self.getTypedRuleContext(SolidityParser.AnnotatedTypeNameContext,0)


        def FinalKeyword(self):
            return self.getToken(SolidityParser.FinalKeyword, 0)

        def identifier(self):
            return self.getTypedRuleContext(SolidityParser.IdentifierContext,0)


        def getRuleIndex(self):
            return SolidityParser.RULE_parameter

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterParameter" ):
                listener.enterParameter(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitParameter" ):
                listener.exitParameter(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitParameter" ):
                return visitor.visitParameter(self)
            else:
                return visitor.visitChildren(self)




    def parameter(self):

        localctx = SolidityParser.ParameterContext(self, self._ctx, self.state)
        self.enterRule(localctx, 32, self.RULE_parameter)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 182
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==SolidityParser.FinalKeyword:
                self.state = 181
                localctx._FinalKeyword = self.match(SolidityParser.FinalKeyword)
                localctx.keywords.append(localctx._FinalKeyword)


            self.state = 184
            localctx.annotated_type = self.annotatedTypeName()
            self.state = 186
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==SolidityParser.Identifier:
                self.state = 185
                localctx.idf = self.identifier()


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class VariableDeclarationContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser
            self._FinalKeyword = None # Token
            self.keywords = list() # of Tokens
            self.annotated_type = None # AnnotatedTypeNameContext
            self.idf = None # IdentifierContext

        def annotatedTypeName(self):
            return self.getTypedRuleContext(SolidityParser.AnnotatedTypeNameContext,0)


        def identifier(self):
            return self.getTypedRuleContext(SolidityParser.IdentifierContext,0)


        def FinalKeyword(self):
            return self.getToken(SolidityParser.FinalKeyword, 0)

        def getRuleIndex(self):
            return SolidityParser.RULE_variableDeclaration

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterVariableDeclaration" ):
                listener.enterVariableDeclaration(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitVariableDeclaration" ):
                listener.exitVariableDeclaration(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitVariableDeclaration" ):
                return visitor.visitVariableDeclaration(self)
            else:
                return visitor.visitChildren(self)




    def variableDeclaration(self):

        localctx = SolidityParser.VariableDeclarationContext(self, self._ctx, self.state)
        self.enterRule(localctx, 34, self.RULE_variableDeclaration)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 189
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==SolidityParser.FinalKeyword:
                self.state = 188
                localctx._FinalKeyword = self.match(SolidityParser.FinalKeyword)
                localctx.keywords.append(localctx._FinalKeyword)


            self.state = 191
            localctx.annotated_type = self.annotatedTypeName()
            self.state = 192
            localctx.idf = self.identifier()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class TypeNameContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def elementaryTypeName(self):
            return self.getTypedRuleContext(SolidityParser.ElementaryTypeNameContext,0)


        def mapping(self):
            return self.getTypedRuleContext(SolidityParser.MappingContext,0)


        def payableAddress(self):
            return self.getTypedRuleContext(SolidityParser.PayableAddressContext,0)


        def getRuleIndex(self):
            return SolidityParser.RULE_typeName

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterTypeName" ):
                listener.enterTypeName(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitTypeName" ):
                listener.exitTypeName(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitTypeName" ):
                return visitor.visitTypeName(self)
            else:
                return visitor.visitChildren(self)




    def typeName(self):

        localctx = SolidityParser.TypeNameContext(self, self._ctx, self.state)
        self.enterRule(localctx, 36, self.RULE_typeName)
        try:
            self.state = 197
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,17,self._ctx)
            if la_ == 1:
                self.enterOuterAlt(localctx, 1)
                self.state = 194
                self.elementaryTypeName()
                pass

            elif la_ == 2:
                self.enterOuterAlt(localctx, 2)
                self.state = 195
                self.mapping()
                pass

            elif la_ == 3:
                self.enterOuterAlt(localctx, 3)
                self.state = 196
                self.payableAddress()
                pass


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ElementaryTypeNameContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser
            self.name = None # Token

        def Uint(self):
            return self.getToken(SolidityParser.Uint, 0)

        def getRuleIndex(self):
            return SolidityParser.RULE_elementaryTypeName

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterElementaryTypeName" ):
                listener.enterElementaryTypeName(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitElementaryTypeName" ):
                listener.exitElementaryTypeName(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitElementaryTypeName" ):
                return visitor.visitElementaryTypeName(self)
            else:
                return visitor.visitChildren(self)




    def elementaryTypeName(self):

        localctx = SolidityParser.ElementaryTypeNameContext(self, self._ctx, self.state)
        self.enterRule(localctx, 38, self.RULE_elementaryTypeName)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 199
            localctx.name = self._input.LT(1)
            _la = self._input.LA(1)
            if not((((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << SolidityParser.T__18) | (1 << SolidityParser.T__19) | (1 << SolidityParser.Uint))) != 0)):
                localctx.name = self._errHandler.recoverInline(self)
            else:
                self._errHandler.reportMatch(self)
                self.consume()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class MappingContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser
            self.key_type = None # ElementaryTypeNameContext
            self.key_label = None # IdentifierContext
            self.value_type = None # AnnotatedTypeNameContext

        def elementaryTypeName(self):
            return self.getTypedRuleContext(SolidityParser.ElementaryTypeNameContext,0)


        def annotatedTypeName(self):
            return self.getTypedRuleContext(SolidityParser.AnnotatedTypeNameContext,0)


        def identifier(self):
            return self.getTypedRuleContext(SolidityParser.IdentifierContext,0)


        def getRuleIndex(self):
            return SolidityParser.RULE_mapping

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterMapping" ):
                listener.enterMapping(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitMapping" ):
                listener.exitMapping(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitMapping" ):
                return visitor.visitMapping(self)
            else:
                return visitor.visitChildren(self)




    def mapping(self):

        localctx = SolidityParser.MappingContext(self, self._ctx, self.state)
        self.enterRule(localctx, 40, self.RULE_mapping)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 201
            self.match(SolidityParser.T__20)
            self.state = 202
            self.match(SolidityParser.T__15)
            self.state = 203
            localctx.key_type = self.elementaryTypeName()
            self.state = 206
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==SolidityParser.T__21:
                self.state = 204
                self.match(SolidityParser.T__21)
                self.state = 205
                localctx.key_label = self.identifier()


            self.state = 208
            self.match(SolidityParser.T__22)
            self.state = 209
            localctx.value_type = self.annotatedTypeName()
            self.state = 210
            self.match(SolidityParser.T__17)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class PayableAddressContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def PayableKeyword(self):
            return self.getToken(SolidityParser.PayableKeyword, 0)

        def getRuleIndex(self):
            return SolidityParser.RULE_payableAddress

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterPayableAddress" ):
                listener.enterPayableAddress(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitPayableAddress" ):
                listener.exitPayableAddress(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitPayableAddress" ):
                return visitor.visitPayableAddress(self)
            else:
                return visitor.visitChildren(self)




    def payableAddress(self):

        localctx = SolidityParser.PayableAddressContext(self, self._ctx, self.state)
        self.enterRule(localctx, 42, self.RULE_payableAddress)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 212
            self.match(SolidityParser.T__18)
            self.state = 213
            self.match(SolidityParser.PayableKeyword)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class StateMutabilityContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def PayableKeyword(self):
            return self.getToken(SolidityParser.PayableKeyword, 0)

        def getRuleIndex(self):
            return SolidityParser.RULE_stateMutability

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterStateMutability" ):
                listener.enterStateMutability(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitStateMutability" ):
                listener.exitStateMutability(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitStateMutability" ):
                return visitor.visitStateMutability(self)
            else:
                return visitor.visitChildren(self)




    def stateMutability(self):

        localctx = SolidityParser.StateMutabilityContext(self, self._ctx, self.state)
        self.enterRule(localctx, 44, self.RULE_stateMutability)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 215
            self.match(SolidityParser.PayableKeyword)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class BlockContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser
            self._statement = None # StatementContext
            self.statements = list() # of StatementContexts

        def statement(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(SolidityParser.StatementContext)
            else:
                return self.getTypedRuleContext(SolidityParser.StatementContext,i)


        def getRuleIndex(self):
            return SolidityParser.RULE_block

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterBlock" ):
                listener.enterBlock(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitBlock" ):
                listener.exitBlock(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitBlock" ):
                return visitor.visitBlock(self)
            else:
                return visitor.visitChildren(self)




    def block(self):

        localctx = SolidityParser.BlockContext(self, self._ctx, self.state)
        self.enterRule(localctx, 46, self.RULE_block)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 217
            self.match(SolidityParser.T__10)
            self.state = 221
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            while ((((_la - 11)) & ~0x3f) == 0 and ((1 << (_la - 11)) & ((1 << (SolidityParser.T__10 - 11)) | (1 << (SolidityParser.T__15 - 11)) | (1 << (SolidityParser.T__18 - 11)) | (1 << (SolidityParser.T__19 - 11)) | (1 << (SolidityParser.T__20 - 11)) | (1 << (SolidityParser.T__21 - 11)) | (1 << (SolidityParser.T__23 - 11)) | (1 << (SolidityParser.T__25 - 11)) | (1 << (SolidityParser.T__26 - 11)) | (1 << (SolidityParser.T__30 - 11)) | (1 << (SolidityParser.T__31 - 11)) | (1 << (SolidityParser.Uint - 11)) | (1 << (SolidityParser.MeKeyword - 11)) | (1 << (SolidityParser.AllKeyword - 11)) | (1 << (SolidityParser.BooleanLiteral - 11)) | (1 << (SolidityParser.DecimalNumber - 11)) | (1 << (SolidityParser.FinalKeyword - 11)) | (1 << (SolidityParser.Identifier - 11)))) != 0):
                self.state = 218
                localctx._statement = self.statement()
                localctx.statements.append(localctx._statement)
                self.state = 223
                self._errHandler.sync(self)
                _la = self._input.LA(1)

            self.state = 224
            self.match(SolidityParser.T__11)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class StatementContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def ifStatement(self):
            return self.getTypedRuleContext(SolidityParser.IfStatementContext,0)


        def whileStatement(self):
            return self.getTypedRuleContext(SolidityParser.WhileStatementContext,0)


        def block(self):
            return self.getTypedRuleContext(SolidityParser.BlockContext,0)


        def returnStatement(self):
            return self.getTypedRuleContext(SolidityParser.ReturnStatementContext,0)


        def simpleStatement(self):
            return self.getTypedRuleContext(SolidityParser.SimpleStatementContext,0)


        def getRuleIndex(self):
            return SolidityParser.RULE_statement

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterStatement" ):
                listener.enterStatement(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitStatement" ):
                listener.exitStatement(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitStatement" ):
                return visitor.visitStatement(self)
            else:
                return visitor.visitChildren(self)




    def statement(self):

        localctx = SolidityParser.StatementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 48, self.RULE_statement)
        try:
            self.state = 231
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [SolidityParser.T__23]:
                self.enterOuterAlt(localctx, 1)
                self.state = 226
                self.ifStatement()
                pass
            elif token in [SolidityParser.T__25]:
                self.enterOuterAlt(localctx, 2)
                self.state = 227
                self.whileStatement()
                pass
            elif token in [SolidityParser.T__10]:
                self.enterOuterAlt(localctx, 3)
                self.state = 228
                self.block()
                pass
            elif token in [SolidityParser.T__26]:
                self.enterOuterAlt(localctx, 4)
                self.state = 229
                self.returnStatement()
                pass
            elif token in [SolidityParser.T__15, SolidityParser.T__18, SolidityParser.T__19, SolidityParser.T__20, SolidityParser.T__21, SolidityParser.T__30, SolidityParser.T__31, SolidityParser.Uint, SolidityParser.MeKeyword, SolidityParser.AllKeyword, SolidityParser.BooleanLiteral, SolidityParser.DecimalNumber, SolidityParser.FinalKeyword, SolidityParser.Identifier]:
                self.enterOuterAlt(localctx, 5)
                self.state = 230
                self.simpleStatement()
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ExpressionStatementContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser
            self.expr = None # ExpressionContext

        def expression(self):
            return self.getTypedRuleContext(SolidityParser.ExpressionContext,0)


        def getRuleIndex(self):
            return SolidityParser.RULE_expressionStatement

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterExpressionStatement" ):
                listener.enterExpressionStatement(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitExpressionStatement" ):
                listener.exitExpressionStatement(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitExpressionStatement" ):
                return visitor.visitExpressionStatement(self)
            else:
                return visitor.visitChildren(self)




    def expressionStatement(self):

        localctx = SolidityParser.ExpressionStatementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 50, self.RULE_expressionStatement)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 233
            localctx.expr = self.expression(0)
            self.state = 234
            self.match(SolidityParser.T__1)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class IfStatementContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser
            self.condition = None # ExpressionContext
            self.then_branch = None # StatementContext
            self.else_branch = None # StatementContext

        def expression(self):
            return self.getTypedRuleContext(SolidityParser.ExpressionContext,0)


        def statement(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(SolidityParser.StatementContext)
            else:
                return self.getTypedRuleContext(SolidityParser.StatementContext,i)


        def getRuleIndex(self):
            return SolidityParser.RULE_ifStatement

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterIfStatement" ):
                listener.enterIfStatement(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitIfStatement" ):
                listener.exitIfStatement(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitIfStatement" ):
                return visitor.visitIfStatement(self)
            else:
                return visitor.visitChildren(self)




    def ifStatement(self):

        localctx = SolidityParser.IfStatementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 52, self.RULE_ifStatement)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 236
            self.match(SolidityParser.T__23)
            self.state = 237
            self.match(SolidityParser.T__15)
            self.state = 238
            localctx.condition = self.expression(0)
            self.state = 239
            self.match(SolidityParser.T__17)
            self.state = 240
            localctx.then_branch = self.statement()
            self.state = 243
            self._errHandler.sync(self)
            la_ = self._interp.adaptivePredict(self._input,21,self._ctx)
            if la_ == 1:
                self.state = 241
                self.match(SolidityParser.T__24)
                self.state = 242
                localctx.else_branch = self.statement()


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class WhileStatementContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser
            self.condition = None # ExpressionContext
            self.body = None # StatementContext

        def expression(self):
            return self.getTypedRuleContext(SolidityParser.ExpressionContext,0)


        def statement(self):
            return self.getTypedRuleContext(SolidityParser.StatementContext,0)


        def getRuleIndex(self):
            return SolidityParser.RULE_whileStatement

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterWhileStatement" ):
                listener.enterWhileStatement(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitWhileStatement" ):
                listener.exitWhileStatement(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitWhileStatement" ):
                return visitor.visitWhileStatement(self)
            else:
                return visitor.visitChildren(self)




    def whileStatement(self):

        localctx = SolidityParser.WhileStatementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 54, self.RULE_whileStatement)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 245
            self.match(SolidityParser.T__25)
            self.state = 246
            self.match(SolidityParser.T__15)
            self.state = 247
            localctx.condition = self.expression(0)
            self.state = 248
            self.match(SolidityParser.T__17)
            self.state = 249
            localctx.body = self.statement()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class SimpleStatementContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def variableDeclarationStatement(self):
            return self.getTypedRuleContext(SolidityParser.VariableDeclarationStatementContext,0)


        def expressionStatement(self):
            return self.getTypedRuleContext(SolidityParser.ExpressionStatementContext,0)


        def getRuleIndex(self):
            return SolidityParser.RULE_simpleStatement

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterSimpleStatement" ):
                listener.enterSimpleStatement(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitSimpleStatement" ):
                listener.exitSimpleStatement(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitSimpleStatement" ):
                return visitor.visitSimpleStatement(self)
            else:
                return visitor.visitChildren(self)




    def simpleStatement(self):

        localctx = SolidityParser.SimpleStatementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 56, self.RULE_simpleStatement)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 253
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [SolidityParser.T__18, SolidityParser.T__19, SolidityParser.T__20, SolidityParser.Uint, SolidityParser.FinalKeyword]:
                self.state = 251
                self.variableDeclarationStatement()
                pass
            elif token in [SolidityParser.T__15, SolidityParser.T__21, SolidityParser.T__30, SolidityParser.T__31, SolidityParser.MeKeyword, SolidityParser.AllKeyword, SolidityParser.BooleanLiteral, SolidityParser.DecimalNumber, SolidityParser.Identifier]:
                self.state = 252
                self.expressionStatement()
                pass
            else:
                raise NoViableAltException(self)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ReturnStatementContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser
            self.expr = None # ExpressionContext

        def expression(self):
            return self.getTypedRuleContext(SolidityParser.ExpressionContext,0)


        def getRuleIndex(self):
            return SolidityParser.RULE_returnStatement

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterReturnStatement" ):
                listener.enterReturnStatement(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitReturnStatement" ):
                listener.exitReturnStatement(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitReturnStatement" ):
                return visitor.visitReturnStatement(self)
            else:
                return visitor.visitChildren(self)




    def returnStatement(self):

        localctx = SolidityParser.ReturnStatementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 58, self.RULE_returnStatement)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 255
            self.match(SolidityParser.T__26)
            self.state = 257
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if ((((_la - 16)) & ~0x3f) == 0 and ((1 << (_la - 16)) & ((1 << (SolidityParser.T__15 - 16)) | (1 << (SolidityParser.T__21 - 16)) | (1 << (SolidityParser.T__30 - 16)) | (1 << (SolidityParser.T__31 - 16)) | (1 << (SolidityParser.MeKeyword - 16)) | (1 << (SolidityParser.AllKeyword - 16)) | (1 << (SolidityParser.BooleanLiteral - 16)) | (1 << (SolidityParser.DecimalNumber - 16)) | (1 << (SolidityParser.Identifier - 16)))) != 0):
                self.state = 256
                localctx.expr = self.expression(0)


            self.state = 259
            self.match(SolidityParser.T__1)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class VariableDeclarationStatementContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser
            self.variable_declaration = None # VariableDeclarationContext
            self.expr = None # ExpressionContext

        def variableDeclaration(self):
            return self.getTypedRuleContext(SolidityParser.VariableDeclarationContext,0)


        def expression(self):
            return self.getTypedRuleContext(SolidityParser.ExpressionContext,0)


        def getRuleIndex(self):
            return SolidityParser.RULE_variableDeclarationStatement

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterVariableDeclarationStatement" ):
                listener.enterVariableDeclarationStatement(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitVariableDeclarationStatement" ):
                listener.exitVariableDeclarationStatement(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitVariableDeclarationStatement" ):
                return visitor.visitVariableDeclarationStatement(self)
            else:
                return visitor.visitChildren(self)




    def variableDeclarationStatement(self):

        localctx = SolidityParser.VariableDeclarationStatementContext(self, self._ctx, self.state)
        self.enterRule(localctx, 60, self.RULE_variableDeclarationStatement)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 261
            localctx.variable_declaration = self.variableDeclaration()
            self.state = 264
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==SolidityParser.T__8:
                self.state = 262
                self.match(SolidityParser.T__8)
                self.state = 263
                localctx.expr = self.expression(0)


            self.state = 266
            self.match(SolidityParser.T__1)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ExpressionContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser


        def getRuleIndex(self):
            return SolidityParser.RULE_expression

     
        def copyFrom(self, ctx:ParserRuleContext):
            super().copyFrom(ctx)


    class AndExprContext(ExpressionContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a SolidityParser.ExpressionContext
            super().__init__(parser)
            self.lhs = None # ExpressionContext
            self.op = None # Token
            self.rhs = None # ExpressionContext
            self.copyFrom(ctx)

        def expression(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(SolidityParser.ExpressionContext)
            else:
                return self.getTypedRuleContext(SolidityParser.ExpressionContext,i)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterAndExpr" ):
                listener.enterAndExpr(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitAndExpr" ):
                listener.exitAndExpr(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitAndExpr" ):
                return visitor.visitAndExpr(self)
            else:
                return visitor.visitChildren(self)


    class MultDivModExprContext(ExpressionContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a SolidityParser.ExpressionContext
            super().__init__(parser)
            self.lhs = None # ExpressionContext
            self.op = None # Token
            self.rhs = None # ExpressionContext
            self.copyFrom(ctx)

        def expression(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(SolidityParser.ExpressionContext)
            else:
                return self.getTypedRuleContext(SolidityParser.ExpressionContext,i)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterMultDivModExpr" ):
                listener.enterMultDivModExpr(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitMultDivModExpr" ):
                listener.exitMultDivModExpr(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitMultDivModExpr" ):
                return visitor.visitMultDivModExpr(self)
            else:
                return visitor.visitChildren(self)


    class ParenthesisExprContext(ExpressionContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a SolidityParser.ExpressionContext
            super().__init__(parser)
            self.expr = None # ExpressionContext
            self.copyFrom(ctx)

        def expression(self):
            return self.getTypedRuleContext(SolidityParser.ExpressionContext,0)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterParenthesisExpr" ):
                listener.enterParenthesisExpr(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitParenthesisExpr" ):
                listener.exitParenthesisExpr(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitParenthesisExpr" ):
                return visitor.visitParenthesisExpr(self)
            else:
                return visitor.visitChildren(self)


    class AllExprContext(ExpressionContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a SolidityParser.ExpressionContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def AllKeyword(self):
            return self.getToken(SolidityParser.AllKeyword, 0)

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterAllExpr" ):
                listener.enterAllExpr(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitAllExpr" ):
                listener.exitAllExpr(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitAllExpr" ):
                return visitor.visitAllExpr(self)
            else:
                return visitor.visitChildren(self)


    class IteExprContext(ExpressionContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a SolidityParser.ExpressionContext
            super().__init__(parser)
            self.cond = None # ExpressionContext
            self.then_expr = None # ExpressionContext
            self.else_expr = None # ExpressionContext
            self.copyFrom(ctx)

        def expression(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(SolidityParser.ExpressionContext)
            else:
                return self.getTypedRuleContext(SolidityParser.ExpressionContext,i)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterIteExpr" ):
                listener.enterIteExpr(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitIteExpr" ):
                listener.exitIteExpr(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitIteExpr" ):
                return visitor.visitIteExpr(self)
            else:
                return visitor.visitChildren(self)


    class PowExprContext(ExpressionContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a SolidityParser.ExpressionContext
            super().__init__(parser)
            self.lhs = None # ExpressionContext
            self.op = None # Token
            self.rhs = None # ExpressionContext
            self.copyFrom(ctx)

        def expression(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(SolidityParser.ExpressionContext)
            else:
                return self.getTypedRuleContext(SolidityParser.ExpressionContext,i)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterPowExpr" ):
                listener.enterPowExpr(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitPowExpr" ):
                listener.exitPowExpr(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitPowExpr" ):
                return visitor.visitPowExpr(self)
            else:
                return visitor.visitChildren(self)


    class PlusMinusExprContext(ExpressionContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a SolidityParser.ExpressionContext
            super().__init__(parser)
            self.lhs = None # ExpressionContext
            self.op = None # Token
            self.rhs = None # ExpressionContext
            self.copyFrom(ctx)

        def expression(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(SolidityParser.ExpressionContext)
            else:
                return self.getTypedRuleContext(SolidityParser.ExpressionContext,i)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterPlusMinusExpr" ):
                listener.enterPlusMinusExpr(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitPlusMinusExpr" ):
                listener.exitPlusMinusExpr(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitPlusMinusExpr" ):
                return visitor.visitPlusMinusExpr(self)
            else:
                return visitor.visitChildren(self)


    class CompExprContext(ExpressionContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a SolidityParser.ExpressionContext
            super().__init__(parser)
            self.lhs = None # ExpressionContext
            self.op = None # Token
            self.rhs = None # ExpressionContext
            self.copyFrom(ctx)

        def expression(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(SolidityParser.ExpressionContext)
            else:
                return self.getTypedRuleContext(SolidityParser.ExpressionContext,i)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterCompExpr" ):
                listener.enterCompExpr(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitCompExpr" ):
                listener.exitCompExpr(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitCompExpr" ):
                return visitor.visitCompExpr(self)
            else:
                return visitor.visitChildren(self)


    class AssignmentExprContext(ExpressionContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a SolidityParser.ExpressionContext
            super().__init__(parser)
            self.lhs = None # ExpressionContext
            self.rhs = None # ExpressionContext
            self.copyFrom(ctx)

        def expression(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(SolidityParser.ExpressionContext)
            else:
                return self.getTypedRuleContext(SolidityParser.ExpressionContext,i)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterAssignmentExpr" ):
                listener.enterAssignmentExpr(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitAssignmentExpr" ):
                listener.exitAssignmentExpr(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitAssignmentExpr" ):
                return visitor.visitAssignmentExpr(self)
            else:
                return visitor.visitChildren(self)


    class OrExprContext(ExpressionContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a SolidityParser.ExpressionContext
            super().__init__(parser)
            self.lhs = None # ExpressionContext
            self.op = None # Token
            self.rhs = None # ExpressionContext
            self.copyFrom(ctx)

        def expression(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(SolidityParser.ExpressionContext)
            else:
                return self.getTypedRuleContext(SolidityParser.ExpressionContext,i)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterOrExpr" ):
                listener.enterOrExpr(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitOrExpr" ):
                listener.exitOrExpr(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitOrExpr" ):
                return visitor.visitOrExpr(self)
            else:
                return visitor.visitChildren(self)


    class IndexExprContext(ExpressionContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a SolidityParser.ExpressionContext
            super().__init__(parser)
            self.arr = None # ExpressionContext
            self.index = None # ExpressionContext
            self.copyFrom(ctx)

        def expression(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(SolidityParser.ExpressionContext)
            else:
                return self.getTypedRuleContext(SolidityParser.ExpressionContext,i)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterIndexExpr" ):
                listener.enterIndexExpr(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitIndexExpr" ):
                listener.exitIndexExpr(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitIndexExpr" ):
                return visitor.visitIndexExpr(self)
            else:
                return visitor.visitChildren(self)


    class SignExprContext(ExpressionContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a SolidityParser.ExpressionContext
            super().__init__(parser)
            self.op = None # Token
            self.expr = None # ExpressionContext
            self.copyFrom(ctx)

        def expression(self):
            return self.getTypedRuleContext(SolidityParser.ExpressionContext,0)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterSignExpr" ):
                listener.enterSignExpr(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitSignExpr" ):
                listener.exitSignExpr(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitSignExpr" ):
                return visitor.visitSignExpr(self)
            else:
                return visitor.visitChildren(self)


    class NumberLiteralExprContext(ExpressionContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a SolidityParser.ExpressionContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def numberLiteral(self):
            return self.getTypedRuleContext(SolidityParser.NumberLiteralContext,0)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterNumberLiteralExpr" ):
                listener.enterNumberLiteralExpr(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitNumberLiteralExpr" ):
                listener.exitNumberLiteralExpr(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitNumberLiteralExpr" ):
                return visitor.visitNumberLiteralExpr(self)
            else:
                return visitor.visitChildren(self)


    class FunctionCallExprContext(ExpressionContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a SolidityParser.ExpressionContext
            super().__init__(parser)
            self.func = None # ExpressionContext
            self.args = None # FunctionCallArgumentsContext
            self.copyFrom(ctx)

        def expression(self):
            return self.getTypedRuleContext(SolidityParser.ExpressionContext,0)

        def functionCallArguments(self):
            return self.getTypedRuleContext(SolidityParser.FunctionCallArgumentsContext,0)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterFunctionCallExpr" ):
                listener.enterFunctionCallExpr(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitFunctionCallExpr" ):
                listener.exitFunctionCallExpr(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitFunctionCallExpr" ):
                return visitor.visitFunctionCallExpr(self)
            else:
                return visitor.visitChildren(self)


    class MemberAccessContext(ExpressionContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a SolidityParser.ExpressionContext
            super().__init__(parser)
            self.expr = None # ExpressionContext
            self.member = None # IdentifierContext
            self.copyFrom(ctx)

        def expression(self):
            return self.getTypedRuleContext(SolidityParser.ExpressionContext,0)

        def identifier(self):
            return self.getTypedRuleContext(SolidityParser.IdentifierContext,0)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterMemberAccess" ):
                listener.enterMemberAccess(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitMemberAccess" ):
                listener.exitMemberAccess(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitMemberAccess" ):
                return visitor.visitMemberAccess(self)
            else:
                return visitor.visitChildren(self)


    class IdentifierExprContext(ExpressionContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a SolidityParser.ExpressionContext
            super().__init__(parser)
            self.idf = None # IdentifierContext
            self.copyFrom(ctx)

        def identifier(self):
            return self.getTypedRuleContext(SolidityParser.IdentifierContext,0)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterIdentifierExpr" ):
                listener.enterIdentifierExpr(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitIdentifierExpr" ):
                listener.exitIdentifierExpr(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitIdentifierExpr" ):
                return visitor.visitIdentifierExpr(self)
            else:
                return visitor.visitChildren(self)


    class EqExprContext(ExpressionContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a SolidityParser.ExpressionContext
            super().__init__(parser)
            self.lhs = None # ExpressionContext
            self.op = None # Token
            self.rhs = None # ExpressionContext
            self.copyFrom(ctx)

        def expression(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(SolidityParser.ExpressionContext)
            else:
                return self.getTypedRuleContext(SolidityParser.ExpressionContext,i)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterEqExpr" ):
                listener.enterEqExpr(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitEqExpr" ):
                listener.exitEqExpr(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitEqExpr" ):
                return visitor.visitEqExpr(self)
            else:
                return visitor.visitChildren(self)


    class BooleanLiteralExprContext(ExpressionContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a SolidityParser.ExpressionContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def BooleanLiteral(self):
            return self.getToken(SolidityParser.BooleanLiteral, 0)

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterBooleanLiteralExpr" ):
                listener.enterBooleanLiteralExpr(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitBooleanLiteralExpr" ):
                listener.exitBooleanLiteralExpr(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitBooleanLiteralExpr" ):
                return visitor.visitBooleanLiteralExpr(self)
            else:
                return visitor.visitChildren(self)


    class MeExprContext(ExpressionContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a SolidityParser.ExpressionContext
            super().__init__(parser)
            self.copyFrom(ctx)

        def MeKeyword(self):
            return self.getToken(SolidityParser.MeKeyword, 0)

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterMeExpr" ):
                listener.enterMeExpr(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitMeExpr" ):
                listener.exitMeExpr(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitMeExpr" ):
                return visitor.visitMeExpr(self)
            else:
                return visitor.visitChildren(self)


    class NotExprContext(ExpressionContext):

        def __init__(self, parser, ctx:ParserRuleContext): # actually a SolidityParser.ExpressionContext
            super().__init__(parser)
            self.expr = None # ExpressionContext
            self.copyFrom(ctx)

        def expression(self):
            return self.getTypedRuleContext(SolidityParser.ExpressionContext,0)


        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterNotExpr" ):
                listener.enterNotExpr(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitNotExpr" ):
                listener.exitNotExpr(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitNotExpr" ):
                return visitor.visitNotExpr(self)
            else:
                return visitor.visitChildren(self)



    def expression(self, _p:int=0):
        _parentctx = self._ctx
        _parentState = self.state
        localctx = SolidityParser.ExpressionContext(self, self._ctx, _parentState)
        _prevctx = localctx
        _startState = 62
        self.enterRecursionRule(localctx, 62, self.RULE_expression, _p)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 282
            self._errHandler.sync(self)
            token = self._input.LA(1)
            if token in [SolidityParser.MeKeyword]:
                localctx = SolidityParser.MeExprContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx

                self.state = 269
                self.match(SolidityParser.MeKeyword)
                pass
            elif token in [SolidityParser.AllKeyword]:
                localctx = SolidityParser.AllExprContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx
                self.state = 270
                self.match(SolidityParser.AllKeyword)
                pass
            elif token in [SolidityParser.T__15]:
                localctx = SolidityParser.ParenthesisExprContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx
                self.state = 271
                self.match(SolidityParser.T__15)
                self.state = 272
                localctx.expr = self.expression(0)
                self.state = 273
                self.match(SolidityParser.T__17)
                pass
            elif token in [SolidityParser.T__30, SolidityParser.T__31]:
                localctx = SolidityParser.SignExprContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx
                self.state = 275
                localctx.op = self._input.LT(1)
                _la = self._input.LA(1)
                if not(_la==SolidityParser.T__30 or _la==SolidityParser.T__31):
                    localctx.op = self._errHandler.recoverInline(self)
                else:
                    self._errHandler.reportMatch(self)
                    self.consume()
                self.state = 276
                localctx.expr = self.expression(14)
                pass
            elif token in [SolidityParser.T__21]:
                localctx = SolidityParser.NotExprContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx
                self.state = 277
                self.match(SolidityParser.T__21)
                self.state = 278
                localctx.expr = self.expression(13)
                pass
            elif token in [SolidityParser.BooleanLiteral]:
                localctx = SolidityParser.BooleanLiteralExprContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx
                self.state = 279
                self.match(SolidityParser.BooleanLiteral)
                pass
            elif token in [SolidityParser.DecimalNumber]:
                localctx = SolidityParser.NumberLiteralExprContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx
                self.state = 280
                self.numberLiteral()
                pass
            elif token in [SolidityParser.Identifier]:
                localctx = SolidityParser.IdentifierExprContext(self, localctx)
                self._ctx = localctx
                _prevctx = localctx
                self.state = 281
                localctx.idf = self.identifier()
                pass
            else:
                raise NoViableAltException(self)

            self._ctx.stop = self._input.LT(-1)
            self.state = 329
            self._errHandler.sync(self)
            _alt = self._interp.adaptivePredict(self._input,27,self._ctx)
            while _alt!=2 and _alt!=ATN.INVALID_ALT_NUMBER:
                if _alt==1:
                    if self._parseListeners is not None:
                        self.triggerExitRuleEvent()
                    _prevctx = localctx
                    self.state = 327
                    self._errHandler.sync(self)
                    la_ = self._interp.adaptivePredict(self._input,26,self._ctx)
                    if la_ == 1:
                        localctx = SolidityParser.PowExprContext(self, SolidityParser.ExpressionContext(self, _parentctx, _parentState))
                        localctx.lhs = _prevctx
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_expression)
                        self.state = 284
                        if not self.precpred(self._ctx, 12):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 12)")
                        self.state = 285
                        localctx.op = self.match(SolidityParser.T__32)
                        self.state = 286
                        localctx.rhs = self.expression(13)
                        pass

                    elif la_ == 2:
                        localctx = SolidityParser.MultDivModExprContext(self, SolidityParser.ExpressionContext(self, _parentctx, _parentState))
                        localctx.lhs = _prevctx
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_expression)
                        self.state = 287
                        if not self.precpred(self._ctx, 11):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 11)")
                        self.state = 288
                        localctx.op = self._input.LT(1)
                        _la = self._input.LA(1)
                        if not((((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << SolidityParser.T__33) | (1 << SolidityParser.T__34) | (1 << SolidityParser.T__35))) != 0)):
                            localctx.op = self._errHandler.recoverInline(self)
                        else:
                            self._errHandler.reportMatch(self)
                            self.consume()
                        self.state = 289
                        localctx.rhs = self.expression(12)
                        pass

                    elif la_ == 3:
                        localctx = SolidityParser.PlusMinusExprContext(self, SolidityParser.ExpressionContext(self, _parentctx, _parentState))
                        localctx.lhs = _prevctx
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_expression)
                        self.state = 290
                        if not self.precpred(self._ctx, 10):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 10)")
                        self.state = 291
                        localctx.op = self._input.LT(1)
                        _la = self._input.LA(1)
                        if not(_la==SolidityParser.T__30 or _la==SolidityParser.T__31):
                            localctx.op = self._errHandler.recoverInline(self)
                        else:
                            self._errHandler.reportMatch(self)
                            self.consume()
                        self.state = 292
                        localctx.rhs = self.expression(11)
                        pass

                    elif la_ == 4:
                        localctx = SolidityParser.CompExprContext(self, SolidityParser.ExpressionContext(self, _parentctx, _parentState))
                        localctx.lhs = _prevctx
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_expression)
                        self.state = 293
                        if not self.precpred(self._ctx, 9):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 9)")
                        self.state = 294
                        localctx.op = self._input.LT(1)
                        _la = self._input.LA(1)
                        if not((((_la) & ~0x3f) == 0 and ((1 << _la) & ((1 << SolidityParser.T__4) | (1 << SolidityParser.T__5) | (1 << SolidityParser.T__6) | (1 << SolidityParser.T__7))) != 0)):
                            localctx.op = self._errHandler.recoverInline(self)
                        else:
                            self._errHandler.reportMatch(self)
                            self.consume()
                        self.state = 295
                        localctx.rhs = self.expression(10)
                        pass

                    elif la_ == 5:
                        localctx = SolidityParser.EqExprContext(self, SolidityParser.ExpressionContext(self, _parentctx, _parentState))
                        localctx.lhs = _prevctx
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_expression)
                        self.state = 296
                        if not self.precpred(self._ctx, 8):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 8)")
                        self.state = 297
                        localctx.op = self._input.LT(1)
                        _la = self._input.LA(1)
                        if not(_la==SolidityParser.T__36 or _la==SolidityParser.T__37):
                            localctx.op = self._errHandler.recoverInline(self)
                        else:
                            self._errHandler.reportMatch(self)
                            self.consume()
                        self.state = 298
                        localctx.rhs = self.expression(9)
                        pass

                    elif la_ == 6:
                        localctx = SolidityParser.AndExprContext(self, SolidityParser.ExpressionContext(self, _parentctx, _parentState))
                        localctx.lhs = _prevctx
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_expression)
                        self.state = 299
                        if not self.precpred(self._ctx, 7):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 7)")
                        self.state = 300
                        localctx.op = self.match(SolidityParser.T__38)
                        self.state = 301
                        localctx.rhs = self.expression(8)
                        pass

                    elif la_ == 7:
                        localctx = SolidityParser.OrExprContext(self, SolidityParser.ExpressionContext(self, _parentctx, _parentState))
                        localctx.lhs = _prevctx
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_expression)
                        self.state = 302
                        if not self.precpred(self._ctx, 6):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 6)")
                        self.state = 303
                        localctx.op = self.match(SolidityParser.T__39)
                        self.state = 304
                        localctx.rhs = self.expression(7)
                        pass

                    elif la_ == 8:
                        localctx = SolidityParser.IteExprContext(self, SolidityParser.ExpressionContext(self, _parentctx, _parentState))
                        localctx.cond = _prevctx
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_expression)
                        self.state = 305
                        if not self.precpred(self._ctx, 5):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 5)")
                        self.state = 306
                        self.match(SolidityParser.T__40)
                        self.state = 307
                        localctx.then_expr = self.expression(0)
                        self.state = 308
                        self.match(SolidityParser.T__41)
                        self.state = 309
                        localctx.else_expr = self.expression(6)
                        pass

                    elif la_ == 9:
                        localctx = SolidityParser.AssignmentExprContext(self, SolidityParser.ExpressionContext(self, _parentctx, _parentState))
                        localctx.lhs = _prevctx
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_expression)
                        self.state = 311
                        if not self.precpred(self._ctx, 4):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 4)")

                        self.state = 312
                        self.match(SolidityParser.T__8)
                        self.state = 313
                        localctx.rhs = self.expression(5)
                        pass

                    elif la_ == 10:
                        localctx = SolidityParser.IndexExprContext(self, SolidityParser.ExpressionContext(self, _parentctx, _parentState))
                        localctx.arr = _prevctx
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_expression)
                        self.state = 314
                        if not self.precpred(self._ctx, 18):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 18)")
                        self.state = 315
                        self.match(SolidityParser.T__27)
                        self.state = 316
                        localctx.index = self.expression(0)
                        self.state = 317
                        self.match(SolidityParser.T__28)
                        pass

                    elif la_ == 11:
                        localctx = SolidityParser.FunctionCallExprContext(self, SolidityParser.ExpressionContext(self, _parentctx, _parentState))
                        localctx.func = _prevctx
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_expression)
                        self.state = 319
                        if not self.precpred(self._ctx, 17):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 17)")
                        self.state = 320
                        self.match(SolidityParser.T__15)
                        self.state = 321
                        localctx.args = self.functionCallArguments()
                        self.state = 322
                        self.match(SolidityParser.T__17)
                        pass

                    elif la_ == 12:
                        localctx = SolidityParser.MemberAccessContext(self, SolidityParser.ExpressionContext(self, _parentctx, _parentState))
                        localctx.expr = _prevctx
                        self.pushNewRecursionContext(localctx, _startState, self.RULE_expression)
                        self.state = 324
                        if not self.precpred(self._ctx, 16):
                            from antlr4.error.Errors import FailedPredicateException
                            raise FailedPredicateException(self, "self.precpred(self._ctx, 16)")
                        self.state = 325
                        self.match(SolidityParser.T__29)
                        self.state = 326
                        localctx.member = self.identifier()
                        pass

             
                self.state = 331
                self._errHandler.sync(self)
                _alt = self._interp.adaptivePredict(self._input,27,self._ctx)

        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.unrollRecursionContexts(_parentctx)
        return localctx


    class FunctionCallArgumentsContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser
            self._expression = None # ExpressionContext
            self.exprs = list() # of ExpressionContexts

        def expression(self, i:int=None):
            if i is None:
                return self.getTypedRuleContexts(SolidityParser.ExpressionContext)
            else:
                return self.getTypedRuleContext(SolidityParser.ExpressionContext,i)


        def getRuleIndex(self):
            return SolidityParser.RULE_functionCallArguments

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterFunctionCallArguments" ):
                listener.enterFunctionCallArguments(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitFunctionCallArguments" ):
                listener.exitFunctionCallArguments(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitFunctionCallArguments" ):
                return visitor.visitFunctionCallArguments(self)
            else:
                return visitor.visitChildren(self)




    def functionCallArguments(self):

        localctx = SolidityParser.FunctionCallArgumentsContext(self, self._ctx, self.state)
        self.enterRule(localctx, 64, self.RULE_functionCallArguments)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 340
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if ((((_la - 16)) & ~0x3f) == 0 and ((1 << (_la - 16)) & ((1 << (SolidityParser.T__15 - 16)) | (1 << (SolidityParser.T__21 - 16)) | (1 << (SolidityParser.T__30 - 16)) | (1 << (SolidityParser.T__31 - 16)) | (1 << (SolidityParser.MeKeyword - 16)) | (1 << (SolidityParser.AllKeyword - 16)) | (1 << (SolidityParser.BooleanLiteral - 16)) | (1 << (SolidityParser.DecimalNumber - 16)) | (1 << (SolidityParser.Identifier - 16)))) != 0):
                self.state = 332
                localctx._expression = self.expression(0)
                localctx.exprs.append(localctx._expression)
                self.state = 337
                self._errHandler.sync(self)
                _la = self._input.LA(1)
                while _la==SolidityParser.T__16:
                    self.state = 333
                    self.match(SolidityParser.T__16)
                    self.state = 334
                    localctx._expression = self.expression(0)
                    localctx.exprs.append(localctx._expression)
                    self.state = 339
                    self._errHandler.sync(self)
                    _la = self._input.LA(1)



        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class ElementaryTypeNameExpressionContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def elementaryTypeName(self):
            return self.getTypedRuleContext(SolidityParser.ElementaryTypeNameContext,0)


        def getRuleIndex(self):
            return SolidityParser.RULE_elementaryTypeNameExpression

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterElementaryTypeNameExpression" ):
                listener.enterElementaryTypeNameExpression(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitElementaryTypeNameExpression" ):
                listener.exitElementaryTypeNameExpression(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitElementaryTypeNameExpression" ):
                return visitor.visitElementaryTypeNameExpression(self)
            else:
                return visitor.visitChildren(self)




    def elementaryTypeNameExpression(self):

        localctx = SolidityParser.ElementaryTypeNameExpressionContext(self, self._ctx, self.state)
        self.enterRule(localctx, 66, self.RULE_elementaryTypeNameExpression)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 342
            self.elementaryTypeName()
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class NumberLiteralContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser

        def DecimalNumber(self):
            return self.getToken(SolidityParser.DecimalNumber, 0)

        def getRuleIndex(self):
            return SolidityParser.RULE_numberLiteral

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterNumberLiteral" ):
                listener.enterNumberLiteral(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitNumberLiteral" ):
                listener.exitNumberLiteral(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitNumberLiteral" ):
                return visitor.visitNumberLiteral(self)
            else:
                return visitor.visitChildren(self)




    def numberLiteral(self):

        localctx = SolidityParser.NumberLiteralContext(self, self._ctx, self.state)
        self.enterRule(localctx, 68, self.RULE_numberLiteral)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 344
            self.match(SolidityParser.DecimalNumber)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class AnnotatedTypeNameContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser
            self.type_name = None # TypeNameContext
            self.privacy_annotation = None # ExpressionContext

        def typeName(self):
            return self.getTypedRuleContext(SolidityParser.TypeNameContext,0)


        def expression(self):
            return self.getTypedRuleContext(SolidityParser.ExpressionContext,0)


        def getRuleIndex(self):
            return SolidityParser.RULE_annotatedTypeName

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterAnnotatedTypeName" ):
                listener.enterAnnotatedTypeName(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitAnnotatedTypeName" ):
                listener.exitAnnotatedTypeName(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitAnnotatedTypeName" ):
                return visitor.visitAnnotatedTypeName(self)
            else:
                return visitor.visitChildren(self)




    def annotatedTypeName(self):

        localctx = SolidityParser.AnnotatedTypeNameContext(self, self._ctx, self.state)
        self.enterRule(localctx, 70, self.RULE_annotatedTypeName)
        self._la = 0 # Token type
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 346
            localctx.type_name = self.typeName()
            self.state = 349
            self._errHandler.sync(self)
            _la = self._input.LA(1)
            if _la==SolidityParser.T__42:
                self.state = 347
                self.match(SolidityParser.T__42)
                self.state = 348
                localctx.privacy_annotation = self.expression(0)


        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx


    class IdentifierContext(ParserRuleContext):

        def __init__(self, parser, parent:ParserRuleContext=None, invokingState:int=-1):
            super().__init__(parent, invokingState)
            self.parser = parser
            self.name = None # Token

        def Identifier(self):
            return self.getToken(SolidityParser.Identifier, 0)

        def getRuleIndex(self):
            return SolidityParser.RULE_identifier

        def enterRule(self, listener:ParseTreeListener):
            if hasattr( listener, "enterIdentifier" ):
                listener.enterIdentifier(self)

        def exitRule(self, listener:ParseTreeListener):
            if hasattr( listener, "exitIdentifier" ):
                listener.exitIdentifier(self)

        def accept(self, visitor:ParseTreeVisitor):
            if hasattr( visitor, "visitIdentifier" ):
                return visitor.visitIdentifier(self)
            else:
                return visitor.visitChildren(self)




    def identifier(self):

        localctx = SolidityParser.IdentifierContext(self, self._ctx, self.state)
        self.enterRule(localctx, 72, self.RULE_identifier)
        try:
            self.enterOuterAlt(localctx, 1)
            self.state = 351
            localctx.name = self.match(SolidityParser.Identifier)
        except RecognitionException as re:
            localctx.exception = re
            self._errHandler.reportError(self, re)
            self._errHandler.recover(self, re)
        finally:
            self.exitRule()
        return localctx



    def sempred(self, localctx:RuleContext, ruleIndex:int, predIndex:int):
        if self._predicates == None:
            self._predicates = dict()
        self._predicates[31] = self.expression_sempred
        pred = self._predicates.get(ruleIndex, None)
        if pred is None:
            raise Exception("No predicate with index:" + str(ruleIndex))
        else:
            return pred(localctx, predIndex)

    def expression_sempred(self, localctx:ExpressionContext, predIndex:int):
            if predIndex == 0:
                return self.precpred(self._ctx, 12)
         

            if predIndex == 1:
                return self.precpred(self._ctx, 11)
         

            if predIndex == 2:
                return self.precpred(self._ctx, 10)
         

            if predIndex == 3:
                return self.precpred(self._ctx, 9)
         

            if predIndex == 4:
                return self.precpred(self._ctx, 8)
         

            if predIndex == 5:
                return self.precpred(self._ctx, 7)
         

            if predIndex == 6:
                return self.precpred(self._ctx, 6)
         

            if predIndex == 7:
                return self.precpred(self._ctx, 5)
         

            if predIndex == 8:
                return self.precpred(self._ctx, 4)
         

            if predIndex == 9:
                return self.precpred(self._ctx, 18)
         

            if predIndex == 10:
                return self.precpred(self._ctx, 17)
         

            if predIndex == 11:
                return self.precpred(self._ctx, 16)
         




