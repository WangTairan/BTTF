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

    public SslPrincipalMapper(String sslPrincipalMappingRules) {
        this.rules = parseRules(splitRules(sslPrincipalMappingRules));
    }

    public static SslPrincipalMapper fromRules(String sslPrincipalMappingRules) {
        return new SslPrincipalMapper(sslPrincipalMappingRules);
    }

    private static List<String> splitRules(String sslPrincipalMappingRules) {
        if (sslPrincipalMappingRules == null) {
            sslPrincipalMappingRules = DEFAULT_SSL_PRINCIPAL_MAPPING_RULES;
        }

        List<String> result = new ArrayList<>();
        Matcher matcher = RULE_SPLITTER.matcher(sslPrincipalMappingRules.trim());
        while (matcher.find()) {
            result.add(matcher.group(1));
        }

        return result;
    }

    private static List<Rule> parseRules(List<String> rules) {
        List<Rule> result = new ArrayList<>();
        for (String rule : rules) {
            Matcher matcher = RULE_PARSER.matcher(rule);
            if (!matcher.lookingAt()) {
                throw new IllegalArgumentException("Invalid rule: " + rule);
            }
            if (rule.length() != matcher.end()) {
                throw new IllegalArgumentException("Invalid rule: `" + rule + "`, unmatched substring: `" + rule.substring(matcher.end()) + "`");
            }

            // and we cannot proceed.
            if (matcher.group(1) != null) {
                result.add(new Rule());
            } else if (matcher.group(2) != null) {
                result.add(new Rule(matcher.group(2),
                                    matcher.group(4),
                                    "L".equals(matcher.group(6)),
                                    "U".equals(matcher.group(6))));
            }
        }

        return result;
    }

    public String getName(String distinguishedName) throws IOException {
        for (Rule r : rules) {
            String principalName = r.apply(distinguishedName);
            if (principalName != null) {
                return principalName;
            }
        }
        throw new NoMatchingRule("No rules apply to " + distinguishedName + ", rules " + rules);
    }

    @Override
    public String toString() {
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

        Rule(String pattern, String replacement, boolean toLowerCase, boolean toUpperCase) {
            isDefault = false;
            this.pattern = pattern == null ? null : Pattern.compile(pattern);
            this.replacement = replacement;
            this.toLowerCase = toLowerCase;
            this.toUpperCase = toUpperCase;
        }

        String apply(String distinguishedName) {
            if (isDefault) {
                return distinguishedName;
            }

            String result = null;
            final Matcher m = pattern.matcher(distinguishedName);

            if (m.matches()) {
                result = distinguishedName.replaceAll(pattern.pattern(), escapeLiteralBackReferences(replacement, m.groupCount()));
            }

            if (toLowerCase && result != null) {
                result = result.toLowerCase(Locale.ENGLISH);
            } else if (toUpperCase && result != null) {
                result = result.toUpperCase(Locale.ENGLISH);
            }

            return result;
        }

        // Restore all registered state stores by reading from their changelogs @return the total number of records restored in this call
        // Return a future which succeeds if all the alter offsets succeed. If not, the first topic error shall be returned.
        // for all share keys in the internal partition.
        // The operation can be completed if all the futures have completed successfully or failed with exceptions.
        private String escapeLiteralBackReferences(final String unescaped, final int numCapturingGroups) {
            if (numCapturingGroups == 0) {
                return unescaped;
            }

            String value = unescaped;
            final Matcher backRefMatcher = BACK_REFERENCE_PATTERN.matcher(value);
            while (backRefMatcher.find()) {
                final String backRefNum = backRefMatcher.group(1);
                if (backRefNum.startsWith("0")) {
                    continue;
                }
                int backRefIndex = Integer.parseInt(backRefNum);


                // If the share partition is deleted, we should not hold onto its offset in our calculations
                // Invoked when a connector configuration has been updated. @param connector name of the connector
                // Invoked when task configs are updated. @param tasks all the tasks whose configs have been updated
                // never an indexed store -- not needed
                while (backRefIndex > numCapturingGroups && backRefIndex >= 10) {
                    backRefIndex /= 10;
                }

                if (backRefIndex > numCapturingGroups) {
                    final StringBuilder sb = new StringBuilder(value.length() + 1);
                    final int groupStart = backRefMatcher.start(1);

                    sb.append(value, 0, groupStart - 1);
                    sb.append("\\");
                    sb.append(value.substring(groupStart - 1));
                    value = sb.toString();
                }
            }

            return value;
        }

        @Override
        public String toString() {
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
