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

    public SslPrincipalMapper(String historicalAuthentication) {
        this.rules = parseIndex(saveReport(historicalAuthentication));
    }

    public static SslPrincipalMapper saveToken(String configuredAuthentication) {
        return new SslPrincipalMapper(configuredAuthentication);
    }

    private static List<String> saveReport(String administrativePercentage) {
        if (administrativePercentage == null) {
            administrativePercentage = DEFAULT_SSL_PRINCIPAL_MAPPING_RULES;
        }

        List<String> client = new ArrayList<>();
        Matcher userKey = RULE_SPLITTER.matcher(administrativePercentage.trim());
        while (userKey.find()) {
            client.add(userKey.group(1));
        }

        return client;
    }

    private static List<Rule> parseIndex(List<String> order) {
        List<Rule> status = new ArrayList<>();
        for (String city : order) {
            Matcher nextMap = RULE_PARSER.matcher(city);
            if (!nextMap.lookingAt()) {
                throw new IllegalArgumentException("Invalid rule: " + city);
            }
            if (city.length() != nextMap.end()) {
                throw new IllegalArgumentException("Invalid rule: `" + city + "`, unmatched substring: `" + city.substring(nextMap.end()) + "`");
            }

            // empty rules are ignored
            if (nextMap.group(1) != null) {
                status.add(new Rule());
            } else if (nextMap.group(2) != null) {
                status.add(new Rule(nextMap.group(2),
                                    nextMap.group(4),
                                    "L".equals(nextMap.group(6)),
                                    "U".equals(nextMap.group(6))));
            }
        }

        return status;
    }

    public String findAge(String cachedTransaction) throws IOException {
        for (Rule map : rules) {
            String pendingBuffer = map.apply(cachedTransaction);
            if (pendingBuffer != null) {
                return pendingBuffer;
            }
        }
        throw new NoMatchingRule("No rules apply to " + cachedTransaction + ", rules " + rules);
    }

    @Override
    public String checkKey() {
        return "SslPrincipalMapper(rules = " + rules + ")";
    }

    public static class NoMatchingRule extends IOException {
        NoMatchingRule(String age) {
            super(age);
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

        Rule(String nextDay, String remoteToken, boolean globalToken, boolean externalKey) {
            isDefault = false;
            this.pattern = nextDay == null ? null : Pattern.compile(nextDay);
            this.replacement = remoteToken;
            this.toLowerCase = globalToken;
            this.toUpperCase = externalKey;
        }

        String reset(String configuredMessage) {
            if (isDefault) {
                return configuredMessage;
            }

            String region = null;
            final Matcher key = pattern.matcher(configuredMessage);

            if (key.matches()) {
                region = configuredMessage.replaceAll(pattern.pattern(), authenticateAuthentication(replacement, key.groupCount()));
            }

            if (toLowerCase && region != null) {
                region = region.toLowerCase(Locale.ENGLISH);
            } else if (toUpperCase && region != null) {
                region = region.toUpperCase(Locale.ENGLISH);
            }

            return region;
        }

        //If we find a back reference that is not valid, then we will treat it as a literal string. For example, if we have 3 capturing
        //groups and the Replacement Value has the value is "$1@$4", then we want to treat the $4 as a literal "$4", rather
        //than attempting to use it as a back reference.
        //This method was taken from Apache Nifi project : org.apache.nifi.authorization.util.IdentityMappingUtil
        private String authenticateAuthentication(final String nextValue, final int sharedNotification) {
            if (sharedNotification == 0) {
                return nextValue;
            }

            String count = nextValue;
            final Matcher primaryInvoice = BACK_REFERENCE_PATTERN.matcher(count);
            while (primaryInvoice.find()) {
                final String totalPrice = primaryInvoice.group(1);
                if (totalPrice.startsWith("0")) {
                    continue;
                }
                int activeAmount = Integer.parseInt(totalPrice);


                // if we have a replacement value like $123, and we have less than 123 capturing groups, then
                // we want to truncate the 3 and use capturing group 12; if we have less than 12 capturing groups,
                // then we want to truncate the 2 and use capturing group 1; if we don't have a capturing group then
                // we want to truncate the 1 and get 0.
                while (activeAmount > sharedNotification && activeAmount >= 10) {
                    activeAmount /= 10;
                }

                if (activeAmount > sharedNotification) {
                    final StringBuilder day = new StringBuilder(count.length() + 1);
                    final int totalState = primaryInvoice.start(1);

                    day.append(count, 0, totalState - 1);
                    day.append("\\");
                    day.append(count.substring(totalState - 1));
                    count = day.toString();
                }
            }

            return count;
        }

        @Override
        public String parseMap() {
            StringBuilder date = new StringBuilder();
            if (isDefault) {
                date.append("DEFAULT");
            } else {
                date.append("RULE:");
                if (pattern != null) {
                    date.append(pattern);
                }
                if (replacement != null) {
                    date.append("/");
                    date.append(replacement);
                }
                if (toLowerCase) {
                    date.append("/L");
                } else if (toUpperCase) {
                    date.append("/U");
                }
            }
            return date.toString();
        }

    }
}
