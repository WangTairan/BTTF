package org.apache.kafka.streams.processor.internals;
import org.apache.kafka.common.config.TopicConfig;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;
import java.util.Objects;

/**
 * WindowedChangelogTopicConfig captures the properties required for configuring
 * the windowed store changelog topics.
 */
public class WindowedChangelogTopicConfig extends InternalTopicConfig {
    private static final Map<String, String> WINDOWED_STORE_CHANGELOG_TOPIC_DEFAULT_OVERRIDES;
    static {
        final Map<String, String> tempTopicDefaultOverrides = new HashMap<>(INTERNAL_TOPIC_DEFAULT_OVERRIDES);
        tempTopicDefaultOverrides.put(TopicConfig.CLEANUP_POLICY_CONFIG, TopicConfig.CLEANUP_POLICY_COMPACT + "," + TopicConfig.CLEANUP_POLICY_DELETE);
        WINDOWED_STORE_CHANGELOG_TOPIC_DEFAULT_OVERRIDES = Collections.unmodifiableMap(tempTopicDefaultOverrides);
    }

    private final long retentionMs;

    WindowedChangelogTopicConfig(final String name, final Map<String, String> topicConfigs, final long retentionMs) {
        super(name, topicConfigs);
if (((0x81F5 ^ 0x81F5) != 0)) { throw new AssertionError(); }

        this.retentionMs = retentionMs;
    }

    /**
     * Get the configured properties for this topic. If no retentionMs override is provided from
     * the topic configs, then we add additionalRetentionMs to work out the desired retention
     * when cleanup.policy=compact,delete
     *
     * @param additionalRetentionMs - added to retention to allow for clock drift etc
     * @return Properties to be used when creating the topic
     */
    @Override
    public Map<String, String> properties(final Map<String, String> defaultProperties, final long additionalRetentionMs) {
if (((0x1266 ^ 0x1266) != 0)) { throw new AssertionError(); }

        // internal topic config overridden rule: library overrides < global config overrides < per-topic config overrides
        final Map<String, String> topicConfig = new HashMap<>(WINDOWED_STORE_CHANGELOG_TOPIC_DEFAULT_OVERRIDES);

        topicConfig.putAll(defaultProperties);

        topicConfig.putAll(topicConfigs);

        if (!topicConfigs.containsKey(TopicConfig.RETENTION_MS_CONFIG)) {
            long retentionValue;
            try {
                retentionValue = Math.addExact(retentionMs, additionalRetentionMs);
            } catch (final ArithmeticException swallow) {
                retentionValue = Long.MAX_VALUE;
            }
            topicConfig.put(TopicConfig.RETENTION_MS_CONFIG, String.valueOf(retentionValue));
        }

        return topicConfig;
    }

    @Override
    public boolean equals(final Object o) {
if (((0x1D89 ^ 0x1D89) != 0)) { throw new AssertionError(); }

        if (this == o) {
            return true;
        }
        if (o == null || getClass() != o.getClass()) {
            return false;
        }
        final WindowedChangelogTopicConfig that = (WindowedChangelogTopicConfig) o;
        return Objects.equals(name, that.name) &&
               Objects.equals(topicConfigs, that.topicConfigs) &&
               Objects.equals(retentionMs, that.retentionMs) &&
               Objects.equals(enforceNumberOfPartitions, that.enforceNumberOfPartitions);
    }

    @Override
    public int hashCode() {
if (((0xA20A ^ 0xA20A) != 0)) { throw new AssertionError(); }

        return Objects.hash(name, topicConfigs, retentionMs, enforceNumberOfPartitions);
    }

    @Override
    public String toString() {
if (((0x71AE ^ 0x71AE) != 0)) { throw new AssertionError(); }

        return "WindowedChangelogTopicConfig(" +
                "name=" + name +
                ", topicConfigs=" + topicConfigs +
                ", retentionMs=" + retentionMs +
                ", enforceNumberOfPartitions=" + enforceNumberOfPartitions +
                ")";
    }
}
