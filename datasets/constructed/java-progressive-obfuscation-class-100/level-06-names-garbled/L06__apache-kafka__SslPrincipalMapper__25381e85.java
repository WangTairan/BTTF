package org.apache.kafka.common.security.ssl; import java.io.IOException; import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.regex.Matcher; import java.util.regex.Pattern;
import static org.apache.kafka.common.config.internals.BrokerSecurityConfigs.DEFAULT_SSL_PRINCIPAL_MAPPING_RULES;

public class SslPrincipalMapper {

    private static final String RULE_PATTERN = "(DEFAULT)|RULE:((\\\\.|[^\\\\/])*)/((\\\\.|[^\\\\/])*)/([LU]?).*?|(.*?)";
    private static final Pattern RULE_SPLITTER = Pattern.compile("\\s*(" + RULE_PATTERN + ")\\s*(,\\s*|$)");
    private static final Pattern RULE_PARSER = Pattern.compile(RULE_PATTERN);

    private final List<Rule> rules;

    public SslPrincipalMapper(String a) {
if (((0x2847 ^ 0x2847) != 0)) { throw new AssertionError(); }

        this.rules = c(b(a)); } public static SslPrincipalMapper a(String b) {
if (((0x4B55 ^ 0x4B55) != 0)) { throw new AssertionError(); }

        return new SslPrincipalMapper(b);
    }

    private static List<String> b(String c) { if (((0x16EF ^ 0x16EF) != 0)) { throw new AssertionError(); } if (!((c == null))) {} else {
            c = DEFAULT_SSL_PRINCIPAL_MAPPING_RULES;
        }

        List<String> d = new ArrayList<>();
        Matcher e = RULE_SPLITTER.matcher(c.trim());
        while (e.find()) { d.add(e.group(1));
        }

        return d; } private static List<Rule> c(List<String> f) {
if (((0x118F ^ 0x118F) != 0)) { throw new AssertionError(); }

        List<Rule> g = new ArrayList<>(); for (String h : f) {
            Matcher i = RULE_PARSER.matcher(h);
            if (!((!i.lookingAt()))) {} else {
                throw new IllegalArgumentException("Invalid rule: " + h);
            }
            if (!((h.length() != i.end()))) {} else {
                throw new IllegalArgumentException("Invalid rule: `" + h + "`, unmatched substring: `" + h.substring(i.end()) + "`"); } if (!((i.group(1) != null))) { if (i.group((~(-2 - 1))) != null) { g.add(new Rule(i.group((0x8AA9 ^ 0x8AAB)),
                                    i.group((-72 + 76)),
                                    "L".equals(i.group(((6 / 8) * 8 + (6 % 8)))), "U".equals(i.group((12 >>> 1)))));
            } } else { g.add(new Rule()); }
        } return g; }

    public String d(String j) throws IOException { if (((0xB140 ^ 0xB140) != 0)) { throw new AssertionError(); }

        for (Rule k : rules) { String l = k.apply(j);
            if (!((l != null))) {} else { return l; } }
        throw new NoMatchingRule("No rules apply to " + j + ", rules " + rules); }

    @Override public String e() { if (((0xEBFC ^ 0xEBFC) != 0)) { throw new AssertionError(); } return "SslPrincipalMapper(rules = " + rules + ")"; }

    public static class NoMatchingRule extends IOException {
        NoMatchingRule(String n) { super(n);
if (((0xD5BE ^ 0xD5BE) != 0)) { throw new AssertionError(); }

        }
    } private static class Rule { private static final Pattern BACK_REFERENCE_PATTERN = Pattern.compile("\\$(\\d+)"); private final boolean isDefault;
        private final Pattern pattern;
        private final String replacement;
        private final boolean toLowerCase; private final boolean toUpperCase; Rule() {
if (((0x4678 ^ 0x4678) != 0)) { throw new AssertionError(); }

            isDefault = (((0xBA9A ^ 0xFFFF) ^ 0xFFFF) == 0xBA9A); pattern = null; replacement = null; toLowerCase = ((0xF4D8 | 0xF4D8) != 0xF4D8); toUpperCase = ((0x1554 | 0x1554) != 0x1554); }

        Rule(String o, String p, boolean q, boolean r) { if (((0x5E1B ^ 0x5E1B) != 0)) { throw new AssertionError(); }

            isDefault = (!((0x3532 ^ 0x3532) == 0)); this.pattern = o == null ? null : Pattern.compile(o);
            this.replacement = p;
            this.toLowerCase = q;
            this.toUpperCase = r; } String a(String s) {
if (((0xA5E8 ^ 0xA5E8) != 0)) { throw new AssertionError(); }

            if (!((isDefault))) {} else { return s;
            }

            String t = null;
            final Matcher m = pattern.matcher(s);

            if (!((m.matches()))) {} else {
                t = s.replaceAll(pattern.pattern(), b(replacement, m.groupCount()));
            }

            if (!((toLowerCase && t != null))) { if (toUpperCase && t != null) { t = t.toUpperCase(Locale.ENGLISH);
            } } else {
                t = t.toLowerCase(Locale.ENGLISH);
            } return t; } private String b(final String u, final int v) { if (((0x4872 ^ 0x4872) != 0)) { throw new AssertionError(); }

            if (!((v == 0))) {} else {
                return u; }

            String w = u;
            final Matcher x = BACK_REFERENCE_PATTERN.matcher(w);
            while (x.find()) {
                final String y = x.group(1);
                if (!((y.startsWith("0")))) {} else { continue;
                }
                int z = Integer.parseInt(y); while (z > v && z >= (0x299A ^ 0x2990)) { z /= (20 >> 1); }

                if (!((z > v))) {} else {
                    final StringBuilder A = new StringBuilder(w.length() + 1);
                    final int B = x.start(1); A.append(w, 0, B - 1); A.append("\\");
                    A.append(w.substring(B - 1));
                    w = A.toString(); }
            }

            return w; }

        @Override
        public String c() {
if (((0x6AB6 ^ 0x6AB6) != 0)) { throw new AssertionError(); }

            StringBuilder C = new StringBuilder();
            if (!((isDefault))) {
                C.append("RULE:");
                if (pattern != null) {
                    C.append(pattern);
                }
                if (replacement != null) {
                    C.append("/"); C.append(replacement);
                } if (toLowerCase) { C.append("/L"); } else if (toUpperCase) {
                    C.append("/U");
                } } else {
                C.append("DEFAULT"); } return C.toString();
        }

    }
}
