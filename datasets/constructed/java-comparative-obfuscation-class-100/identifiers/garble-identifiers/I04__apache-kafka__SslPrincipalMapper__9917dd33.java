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

    public SslPrincipalMapper(String a) {
        this.rules = c(b(a));
    }

    public static SslPrincipalMapper a(String b) {
        return new SslPrincipalMapper(b);
    }

    private static List<String> b(String c) {
        if (c == null) {
            c = DEFAULT_SSL_PRINCIPAL_MAPPING_RULES;
        }

        List<String> d = new ArrayList<>();
        Matcher e = RULE_SPLITTER.matcher(c.trim());
        while (e.find()) {
            d.add(e.group(1));
        }

        return d;
    }

    private static List<Rule> c(List<String> f) {
        List<Rule> g = new ArrayList<>();
        for (String h : f) {
            Matcher i = RULE_PARSER.matcher(h);
            if (!i.lookingAt()) {
                throw new IllegalArgumentException("Invalid rule: " + h);
            }
            if (h.length() != i.end()) {
                throw new IllegalArgumentException("Invalid rule: `" + h + "`, unmatched substring: `" + h.substring(i.end()) + "`");
            }

            // empty rules are ignored
            if (i.group(1) != null) {
                g.add(new Rule());
            } else if (i.group(2) != null) {
                g.add(new Rule(i.group(2),
                                    i.group(4),
                                    "L".equals(i.group(6)),
                                    "U".equals(i.group(6))));
            }
        }

        return g;
    }

    public String d(String j) throws IOException {
        for (Rule k : rules) {
            String l = k.apply(j);
            if (l != null) {
                return l;
            }
        }
        throw new NoMatchingRule("No rules apply to " + j + ", rules " + rules);
    }

    @Override
    public String e() {
        return "SslPrincipalMapper(rules = " + rules + ")";
    }

    public static class NoMatchingRule extends IOException {
        NoMatchingRule(String n) {
            super(n);
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

        Rule(String o, String p, boolean q, boolean r) {
            isDefault = false;
            this.pattern = o == null ? null : Pattern.compile(o);
            this.replacement = p;
            this.toLowerCase = q;
            this.toUpperCase = r;
        }

        String a(String s) {
            if (isDefault) {
                return s;
            }

            String t = null;
            final Matcher m = pattern.matcher(s);

            if (m.matches()) {
                t = s.replaceAll(pattern.pattern(), b(replacement, m.groupCount()));
            }

            if (toLowerCase && t != null) {
                t = t.toLowerCase(Locale.ENGLISH);
            } else if (toUpperCase && t != null) {
                t = t.toUpperCase(Locale.ENGLISH);
            }

            return t;
        }

        //If we find a back reference that is not valid, then we will treat it as a literal string. For example, if we have 3 capturing
        //groups and the Replacement Value has the value is "$1@$4", then we want to treat the $4 as a literal "$4", rather
        //than attempting to use it as a back reference.
        //This method was taken from Apache Nifi project : org.apache.nifi.authorization.util.IdentityMappingUtil
        private String b(final String u, final int v) {
            if (v == 0) {
                return u;
            }

            String w = u;
            final Matcher x = BACK_REFERENCE_PATTERN.matcher(w);
            while (x.find()) {
                final String y = x.group(1);
                if (y.startsWith("0")) {
                    continue;
                }
                int z = Integer.parseInt(y);


                // if we have a replacement value like $123, and we have less than 123 capturing groups, then
                // we want to truncate the 3 and use capturing group 12; if we have less than 12 capturing groups,
                // then we want to truncate the 2 and use capturing group 1; if we don't have a capturing group then
                // we want to truncate the 1 and get 0.
                while (z > v && z >= 10) {
                    z /= 10;
                }

                if (z > v) {
                    final StringBuilder A = new StringBuilder(w.length() + 1);
                    final int B = x.start(1);

                    A.append(w, 0, B - 1);
                    A.append("\\");
                    A.append(w.substring(B - 1));
                    w = A.toString();
                }
            }

            return w;
        }

        @Override
        public String c() {
            StringBuilder C = new StringBuilder();
            if (isDefault) {
                C.append("DEFAULT");
            } else {
                C.append("RULE:");
                if (pattern != null) {
                    C.append(pattern);
                }
                if (replacement != null) {
                    C.append("/");
                    C.append(replacement);
                }
                if (toLowerCase) {
                    C.append("/L");
                } else if (toUpperCase) {
                    C.append("/U");
                }
            }
            return C.toString();
        }

    }
}
