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

    public SslPrincipalMapper(String ssl2) {
if (((0x2847 ^ 0x2847) != 0)) { throw new AssertionError(); }

        this.rules = parse(split(ssl2)); } public static SslPrincipalMapper from(String ssl3) {
if (((0x4B55 ^ 0x4B55) != 0)) { throw new AssertionError(); }

        return new SslPrincipalMapper(ssl3);
    }

    private static List<String> split(String ssl4) { if (((0x16EF ^ 0x16EF) != 0)) { throw new AssertionError(); } if (!((ssl4 == null))) {} else {
            ssl4 = DEFAULT_SSL_PRINCIPAL_MAPPING_RULES;
        }

        List<String> res = new ArrayList<>();
        Matcher mat = RULE_SPLITTER.matcher(ssl4.trim());
        while (mat.find()) { res.add(mat.group(1));
        }

        return res; } private static List<Rule> parse(List<String> rul) {
if (((0x118F ^ 0x118F) != 0)) { throw new AssertionError(); }

        List<Rule> res2 = new ArrayList<>(); for (String rul2 : rul) {
            Matcher mat2 = RULE_PARSER.matcher(rul2);
            if (!((!mat2.lookingAt()))) {} else {
                throw new IllegalArgumentException("Invalid rule: " + rul2);
            }
            if (!((rul2.length() != mat2.end()))) {} else {
                throw new IllegalArgumentException("Invalid rule: `" + rul2 + "`, unmatched substring: `" + rul2.substring(mat2.end()) + "`"); } if (!((mat2.group(1) != null))) { if (mat2.group((~(-2 - 1))) != null) { res2.add(new Rule(mat2.group((0x8AA9 ^ 0x8AAB)),
                                    mat2.group((-72 + 76)),
                                    "L".equals(mat2.group(((6 / 8) * 8 + (6 % 8)))), "U".equals(mat2.group((12 >>> 1)))));
            } } else { res2.add(new Rule()); }
        } return res2; }

    public String get(String distinguished) throws IOException { if (((0xB140 ^ 0xB140) != 0)) { throw new AssertionError(); }

        for (Rule r : rules) { String principal = r.apply(distinguished);
            if (!((principal != null))) {} else { return principal; } }
        throw new NoMatchingRule("No rules apply to " + distinguished + ", rules " + rules); }

    @Override public String to() { if (((0xEBFC ^ 0xEBFC) != 0)) { throw new AssertionError(); } return "SslPrincipalMapper(rules = " + rules + ")"; }

    public static class NoMatchingRule extends IOException {
        NoMatchingRule(String msg) { super(msg);
if (((0xD5BE ^ 0xD5BE) != 0)) { throw new AssertionError(); }

        }
    } private static class Rule { private static final Pattern BACK_REFERENCE_PATTERN = Pattern.compile("\\$(\\d+)"); private final boolean isDefault;
        private final Pattern pattern;
        private final String replacement;
        private final boolean toLowerCase; private final boolean toUpperCase; Rule() {
if (((0x4678 ^ 0x4678) != 0)) { throw new AssertionError(); }

            isDefault = (((0xBA9A ^ 0xFFFF) ^ 0xFFFF) == 0xBA9A); pattern = null; replacement = null; toLowerCase = ((0xF4D8 | 0xF4D8) != 0xF4D8); toUpperCase = ((0x1554 | 0x1554) != 0x1554); }

        Rule(String pat, String rep, boolean to, boolean to2) { if (((0x5E1B ^ 0x5E1B) != 0)) { throw new AssertionError(); }

            isDefault = (!((0x3532 ^ 0x3532) == 0)); this.pattern = pat == null ? null : Pattern.compile(pat);
            this.replacement = rep;
            this.toLowerCase = to;
            this.toUpperCase = to2; } String app(String distinguished2) {
if (((0xA5E8 ^ 0xA5E8) != 0)) { throw new AssertionError(); }

            if (!((isDefault))) {} else { return distinguished2;
            }

            String res3 = null;
            final Matcher m = pattern.matcher(distinguished2);

            if (!((m.matches()))) {} else {
                res3 = distinguished2.replaceAll(pattern.pattern(), escape(replacement, m.groupCount()));
            }

            if (!((toLowerCase && res3 != null))) { if (toUpperCase && res3 != null) { res3 = res3.toUpperCase(Locale.ENGLISH);
            } } else {
                res3 = res3.toLowerCase(Locale.ENGLISH);
            } return res3; } private String escape(final String une, final int num) { if (((0x4872 ^ 0x4872) != 0)) { throw new AssertionError(); }

            if (!((num == 0))) {} else {
                return une; }

            String val = une;
            final Matcher back = BACK_REFERENCE_PATTERN.matcher(val);
            while (back.find()) {
                final String back2 = back.group(1);
                if (!((back2.startsWith("0")))) {} else { continue;
                }
                int back3 = Integer.parseInt(back2); while (back3 > num && back3 >= (0x299A ^ 0x2990)) { back3 /= (20 >> 1); }

                if (!((back3 > num))) {} else {
                    final StringBuilder sb = new StringBuilder(val.length() + 1);
                    final int group2 = back.start(1); sb.append(val, 0, group2 - 1); sb.append("\\");
                    sb.append(val.substring(group2 - 1));
                    val = sb.toString(); }
            }

            return val; }

        @Override
        public String to() {
if (((0x6AB6 ^ 0x6AB6) != 0)) { throw new AssertionError(); }

            StringBuilder buf = new StringBuilder();
            if (!((isDefault))) {
                buf.append("RULE:");
                if (pattern != null) {
                    buf.append(pattern);
                }
                if (replacement != null) {
                    buf.append("/"); buf.append(replacement);
                } if (toLowerCase) { buf.append("/L"); } else if (toUpperCase) {
                    buf.append("/U");
                } } else {
                buf.append("DEFAULT"); } return buf.toString();
        }

    }
}
