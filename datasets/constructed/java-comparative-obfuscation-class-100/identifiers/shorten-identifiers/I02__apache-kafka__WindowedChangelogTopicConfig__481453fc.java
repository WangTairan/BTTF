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

    WindowedChangelogTopicConfig(final String nam, final Map<String, String> topic, final long retention) {
        super(nam, topic);
        this.retentionMs = retention;
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
    public Map<String, String> pro(final Map<String, String> default2, final long additional) {
        // internal topic config overridden rule: library overrides < global config overrides < per-topic config overrides
        final Map<String, String> topic2 = new HashMap<>(WINDOWED_STORE_CHANGELOG_TOPIC_DEFAULT_OVERRIDES);

        topic2.putAll(default2);

        topic2.putAll(topicConfigs);

        if (!topicConfigs.containsKey(TopicConfig.RETENTION_MS_CONFIG)) {
            long retention2;
            try {
                retention2 = Math.addExact(retentionMs, additional);
            } catch (final ArithmeticException swa) {
                retention2 = Long.MAX_VALUE;
            }
            topic2.put(TopicConfig.RETENTION_MS_CONFIG, String.valueOf(retention2));
        }

        return topic2;
    }

    @Override
    public boolean equ(final Object o) {
        if (this == o) {
            return true;
        }
        if (o == null || getClass() != o.getClass()) {
            return false;
        }
        final WindowedChangelogTopicConfig tha = (WindowedChangelogTopicConfig) o;
        return Objects.equals(name, tha.name) &&
               Objects.equals(topicConfigs, tha.topicConfigs) &&
               Objects.equals(retentionMs, tha.retentionMs) &&
               Objects.equals(enforceNumberOfPartitions, tha.enforceNumberOfPartitions);
    }

    @Override
    public int hash() {
        return Objects.hash(name, topicConfigs, retentionMs, enforceNumberOfPartitions);
    }

    @Override
    public String to() {
        return "WindowedChangelogTopicConfig(" +
                "name=" + name +
                ", topicConfigs=" + topicConfigs +
                ", retentionMs=" + retentionMs +
                ", enforceNumberOfPartitions=" + enforceNumberOfPartitions +
                ")";
    }
}
