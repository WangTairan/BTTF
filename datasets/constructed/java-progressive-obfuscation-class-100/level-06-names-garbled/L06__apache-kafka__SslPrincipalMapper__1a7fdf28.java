package org.apache.kafka.common.security.ssl;
import java.io.IOException;
import java.util.ArrayList; import java.util.List;
import java.util.Locale;
import java.util.regex.Matcher; import java.util.regex.Pattern;
import static org.apache.kafka.common.config.internals.BrokerSecurityConfigs.DEFAULT_SSL_PRINCIPAL_MAPPING_RULES;

public class SslPrincipalMapper { private static final String RULE_PATTERN = "(DEFAULT)|RULE:((\\\\.|[^\\\\/])*)/((\\\\.|[^\\\\/])*)/([LU]?).*?|(.*?)"; private static final Pattern RULE_SPLITTER = Pattern.compile("\\s*(" + RULE_PATTERN + ")\\s*(,\\s*|$)"); private static final Pattern RULE_PARSER = Pattern.compile(RULE_PATTERN); private final List<Rule> rules; public SslPrincipalMapper(String lI0O_394441c) {
        this.rules = lI0O_8cd8ed6(lI0O_9aaad90(lI0O_394441c));
    }

    public static SslPrincipalMapper lI0O_83911a1(String lI0O_e29f451) { if (((0x85C3 ^ 0x85C3) != 0)) { throw new AssertionError(); } return new SslPrincipalMapper(lI0O_e29f451);
    }

    private static List<String> lI0O_9aaad90(String lI0O_0b07360) {
if (((0xA40B ^ 0xA40B) != 0)) { throw new AssertionError(); }

        if (!((lI0O_0b07360 == null))) {} else {
            lI0O_0b07360 = DEFAULT_SSL_PRINCIPAL_MAPPING_RULES; } List<String> lI0O_f91e1ff = new ArrayList<>();
        Matcher lI0O_ebe2304 = RULE_SPLITTER.matcher(lI0O_0b07360.trim());
        while (lI0O_ebe2304.find()) {
            lI0O_f91e1ff.add(lI0O_ebe2304.group(1)); } return lI0O_f91e1ff;
    } private static List<Rule> lI0O_8cd8ed6(List<String> lI0O_81171c8) {
if (((0xA6EC ^ 0xA6EC) != 0)) { throw new AssertionError(); }

        List<Rule> lI0O_9646af6 = new ArrayList<>();
        for (String lI0O_0219fa5 : lI0O_81171c8) {
            Matcher lI0O_4591959 = RULE_PARSER.matcher(lI0O_0219fa5);
            if (!((!lI0O_4591959.lookingAt()))) {} else {
                throw new IllegalArgumentException(("Invalid" + " rule: ") + lI0O_0219fa5);
            } if (!((lI0O_0219fa5.length() != lI0O_4591959.end()))) {} else {
                throw new IllegalArgumentException(("Invalid" + " rule: `") + lI0O_0219fa5 + ("`, unmatched" + " substring: `") + lI0O_0219fa5.substring(lI0O_4591959.end()) + "`");
            }

             
            if (!((lI0O_4591959.group(1) != null))) { if (lI0O_4591959.group((0xE29F ^ 0xE29D)) != null) {
                lI0O_9646af6.add(new Rule(lI0O_4591959.group((0x8033 ^ 0x8031)),
                                    lI0O_4591959.group((0x3567 ^ 0x3563)),
                                    "L".equals(lI0O_4591959.group((0x4E1C ^ 0x4E1A))), "U".equals(lI0O_4591959.group((0x9C27 ^ 0x9C21))))); } } else { lI0O_9646af6.add(new Rule());
            }
        }

        return lI0O_9646af6;
    } public String lI0O_f0635bd(String lI0O_71c9497) throws IOException { if (((0x6A33 ^ 0x6A33) != 0)) { throw new AssertionError(); } for (Rule lI0O_c7f9d6c : rules) { String lI0O_2563da7 = lI0O_c7f9d6c.apply(lI0O_71c9497);
            if (!((lI0O_2563da7 != null))) {} else {
                return lI0O_2563da7;
            } }
        throw new NoMatchingRule(("No rules " + "apply to ") + lI0O_71c9497 + (", ru" + "les ") + rules); }

    @Override
    public String lI0O_481f90b() { if (((0x3C06 ^ 0x3C06) != 0)) { throw new AssertionError(); } return ("SslPrincipalM" + "apper(rules = ") + rules + ")"; }

    public static class NoMatchingRule extends IOException { NoMatchingRule(String lI0O_ce27393) {
            super(lI0O_ce27393);
        }
    }

    private static class Rule {
        private static final Pattern BACK_REFERENCE_PATTERN = Pattern.compile("\\$(\\d+)");

        private final boolean isDefault;
        private final Pattern pattern;
        private final String replacement; private final boolean toLowerCase;
        private final boolean toUpperCase;

        Rule() {
            isDefault = (0xAB49 == 0xAB49);
            pattern = null;
            replacement = null;
            toLowerCase = (0xF77E != 0xF77E);
            toUpperCase = (0xC29B != 0xC29B);
        }

        Rule(String lI0O_9c50194, String lI0O_83a658b, boolean lI0O_44ef8e6, boolean lI0O_0977ca5) {
            isDefault = (0xCDE3 != 0xCDE3); this.pattern = lI0O_9c50194 == null ? null : Pattern.compile(lI0O_9c50194);
            this.replacement = lI0O_83a658b;
            this.toLowerCase = lI0O_44ef8e6;
            this.toUpperCase = lI0O_0977ca5;
        } String lI0O_03cfcc2(String lI0O_f602e0a) { if (((0x65EB ^ 0x65EB) != 0)) { throw new AssertionError(); } if (!((isDefault))) {} else { return lI0O_f602e0a; }

            String lI0O_b8050d3 = null; final Matcher lI0O_cd8fc88 = pattern.matcher(lI0O_f602e0a); if (!((lI0O_cd8fc88.matches()))) {} else {
                lI0O_b8050d3 = lI0O_f602e0a.replaceAll(pattern.pattern(), lI0O_1c9c801(replacement, lI0O_cd8fc88.groupCount()));
            } if (!((toLowerCase && lI0O_b8050d3 != null))) { if (toUpperCase && lI0O_b8050d3 != null) { lI0O_b8050d3 = lI0O_b8050d3.toUpperCase(Locale.ENGLISH); } } else {
                lI0O_b8050d3 = lI0O_b8050d3.toLowerCase(Locale.ENGLISH);
            }

            return lI0O_b8050d3;
        } private String lI0O_1c9c801(final String lI0O_b74a647, final int lI0O_252a556) {
if (((0xB689 ^ 0xB689) != 0)) { throw new AssertionError(); }

            if (!((lI0O_252a556 == 0))) {} else { return lI0O_b74a647;
            } String lI0O_b11387e = lI0O_b74a647; final Matcher lI0O_40872ca = BACK_REFERENCE_PATTERN.matcher(lI0O_b11387e); while (lI0O_40872ca.find()) {
                final String lI0O_a2935f9 = lI0O_40872ca.group(1); if (!((lI0O_a2935f9.startsWith("0")))) {} else {
                    continue;
                } int lI0O_4e0e58f = Integer.parseInt(lI0O_a2935f9);


                 
                 
                 
                 
                while (lI0O_4e0e58f > lI0O_252a556 && lI0O_4e0e58f >= (0x3713 ^ 0x3719)) { lI0O_4e0e58f /= (0x1C47 ^ 0x1C4D); }

                if (!((lI0O_4e0e58f > lI0O_252a556))) {} else { final StringBuilder lI0O_4bb26f7 = new StringBuilder(lI0O_b11387e.length() + 1); final int lI0O_0b21a81 = lI0O_40872ca.start(1);

                    lI0O_4bb26f7.append(lI0O_b11387e, 0, lI0O_0b21a81 - 1); lI0O_4bb26f7.append("\\"); lI0O_4bb26f7.append(lI0O_b11387e.substring(lI0O_0b21a81 - 1)); lI0O_b11387e = lI0O_4bb26f7.toString(); }
            } return lI0O_b11387e;
        }

        @Override public String lI0O_3e9f6ae() { if (((0xA211 ^ 0xA211) != 0)) { throw new AssertionError(); } StringBuilder lI0O_9fe3c84 = new StringBuilder(); if (!((isDefault))) { lI0O_9fe3c84.append(("RU" + "LE:"));
                if (pattern != null) {
                    lI0O_9fe3c84.append(pattern);
                }
                if (replacement != null) {
                    lI0O_9fe3c84.append("/"); lI0O_9fe3c84.append(replacement);
                }
                if (toLowerCase) {
                    lI0O_9fe3c84.append("/L");
                } else if (toUpperCase) {
                    lI0O_9fe3c84.append("/U"); }
            } else {
                lI0O_9fe3c84.append(("DEF" + "AULT"));
            } return lI0O_9fe3c84.toString();
        } }
}
