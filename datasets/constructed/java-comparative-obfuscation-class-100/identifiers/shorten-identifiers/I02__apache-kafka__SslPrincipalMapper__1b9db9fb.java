package org.apache.kafka.common.security.ssl;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import static org.apache.kafka.common.config.internals.BrokerSecurityConfigs.DEFAULT_SSL_PRINCIPAL_MAPPING_RULES;

public class SslPrincipalMapper {

    private static final String RULE_PATTERN = "(DEFAULT)|RULE:((\\\\.|[^\\\\/])*)/((\\\\.|[^\\\\/])*)/([LU]?).*?|(.*?)";
    private static final Pattern RULE_SPLITTER = Pattern.compile("\\s*(" + RULE_PATTERN + ")\\s*(,\\s*|$)");
    private static final Pattern RULE_PARSER = Pattern.compile(RULE_PATTERN);

    private final List<Rule> rules;

    public SslPrincipalMapper(String ssl2) {
        this.rules = parse(split(ssl2));
    }

    public static SslPrincipalMapper from(String ssl3) {
        return new SslPrincipalMapper(ssl3);
    }

    private static List<String> split(String ssl4) {
        if (ssl4 == null) {
            ssl4 = DEFAULT_SSL_PRINCIPAL_MAPPING_RULES;
        }

        List<String> res = new ArrayList<>();
        Matcher mat = RULE_SPLITTER.matcher(ssl4.trim());
        while (mat.find()) {
            res.add(mat.group(1));
        }

        return res;
    }

    private static List<Rule> parse(List<String> rul) {
        List<Rule> res2 = new ArrayList<>();
        for (String rul2 : rul) {
            Matcher mat2 = RULE_PARSER.matcher(rul2);
            if (!mat2.lookingAt()) {
                throw new IllegalArgumentException("Invalid rule: " + rul2);
            }
            if (rul2.length() != mat2.end()) {
                throw new IllegalArgumentException("Invalid rule: `" + rul2 + "`, unmatched substring: `" + rul2.substring(mat2.end()) + "`");
            }

            // empty rules are ignored
            if (mat2.group(1) != null) {
                res2.add(new Rule());
            } else if (mat2.group(2) != null) {
                res2.add(new Rule(mat2.group(2),
                                    mat2.group(4),
                                    "L".equals(mat2.group(6)),
                                    "U".equals(mat2.group(6))));
            }
        }

        return res2;
    }

    public String get(String distinguished) throws IOException {
        for (Rule r : rules) {
            String principal = r.apply(distinguished);
            if (principal != null) {
                return principal;
            }
        }
        throw new NoMatchingRule("No rules apply to " + distinguished + ", rules " + rules);
    }

    @Override
    public String to() {
        return "SslPrincipalMapper(rules = " + rules + ")";
    }

    public static class NoMatchingRule extends IOException {
        NoMatchingRule(String msg) {
            super(msg);
        }
    }

    private static class Rule {
        private static final Pattern BACK_REFERENCE_PATTERN = Pattern.compile("\\$(\\d+)");

        private final boolean isDefault;
        private final Pattern pattern;
        private final String replacement;
        private final boolean toLowerCase;
        private final boolean toUpperCase;

        Rule() {
            isDefault = true;
            pattern = null;
            replacement = null;
            toLowerCase = false;
            toUpperCase = false;
        }

        Rule(String pat, String rep, boolean to, boolean to2) {
            isDefault = false;
            this.pattern = pat == null ? null : Pattern.compile(pat);
            this.replacement = rep;
            this.toLowerCase = to;
            this.toUpperCase = to2;
        }

        String app(String distinguished2) {
            if (isDefault) {
                return distinguished2;
            }

            String res3 = null;
            final Matcher m = pattern.matcher(distinguished2);

            if (m.matches()) {
                res3 = distinguished2.replaceAll(pattern.pattern(), escape(replacement, m.groupCount()));
            }

            if (toLowerCase && res3 != null) {
                res3 = res3.toLowerCase(Locale.ENGLISH);
            } else if (toUpperCase && res3 != null) {
                res3 = res3.toUpperCase(Locale.ENGLISH);
            }

            return res3;
        }

        //If we find a back reference that is not valid, then we will treat it as a literal string. For example, if we have 3 capturing
        //groups and the Replacement Value has the value is "$1@$4", then we want to treat the $4 as a literal "$4", rather
        //than attempting to use it as a back reference.
        //This method was taken from Apache Nifi project : org.apache.nifi.authorization.util.IdentityMappingUtil
        private String escape(final String une, final int num) {
            if (num == 0) {
                return une;
            }

            String val = une;
            final Matcher back = BACK_REFERENCE_PATTERN.matcher(val);
            while (back.find()) {
                final String back2 = back.group(1);
                if (back2.startsWith("0")) {
                    continue;
                }
                int back3 = Integer.parseInt(back2);


                // if we have a replacement value like $123, and we have less than 123 capturing groups, then
                // we want to truncate the 3 and use capturing group 12; if we have less than 12 capturing groups,
                // then we want to truncate the 2 and use capturing group 1; if we don't have a capturing group then
                // we want to truncate the 1 and get 0.
                while (back3 > num && back3 >= 10) {
                    back3 /= 10;
                }

                if (back3 > num) {
                    final StringBuilder sb = new StringBuilder(val.length() + 1);
                    final int group2 = back.start(1);

                    sb.append(val, 0, group2 - 1);
                    sb.append("\\");
                    sb.append(val.substring(group2 - 1));
                    val = sb.toString();
                }
            }

            return val;
        }

        @Override
        public String to() {
            StringBuilder buf = new StringBuilder();
            if (isDefault) {
                buf.append("DEFAULT");
            } else {
                buf.append("RULE:");
                if (pattern != null) {
                    buf.append(pattern);
                }
                if (replacement != null) {
                    buf.append("/");
                    buf.append(replacement);
                }
                if (toLowerCase) {
                    buf.append("/L");
                } else if (toUpperCase) {
                    buf.append("/U");
                }
            }
            return buf.toString();
        }

    }
}
