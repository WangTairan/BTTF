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

    WindowedChangelogTopicConfig(final String a, final Map<String, String> b, final long c) {
        super(a, b);
        this.retentionMs = c;
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
    public Map<String, String> a(final Map<String, String> d, final long e) {
        // internal topic config overridden rule: library overrides < global config overrides < per-topic config overrides
        final Map<String, String> f = new HashMap<>(WINDOWED_STORE_CHANGELOG_TOPIC_DEFAULT_OVERRIDES);

        f.putAll(d);

        f.putAll(topicConfigs);

        if (!topicConfigs.containsKey(TopicConfig.RETENTION_MS_CONFIG)) {
            long g;
            try {
                g = Math.addExact(retentionMs, e);
            } catch (final ArithmeticException h) {
                g = Long.MAX_VALUE;
            }
            f.put(TopicConfig.RETENTION_MS_CONFIG, String.valueOf(g));
        }

        return f;
    }

    @Override
    public boolean b(final Object i) {
        if (this == i) {
            return true;
        }
        if (i == null || getClass() != i.getClass()) {
            return false;
        }
        final WindowedChangelogTopicConfig j = (WindowedChangelogTopicConfig) i;
        return Objects.equals(name, j.name) &&
               Objects.equals(topicConfigs, j.topicConfigs) &&
               Objects.equals(retentionMs, j.retentionMs) &&
               Objects.equals(enforceNumberOfPartitions, j.enforceNumberOfPartitions);
    }

    @Override
    public int c() {
        return Objects.hash(name, topicConfigs, retentionMs, enforceNumberOfPartitions);
    }

    @Override
    public String d() {
        return "WindowedChangelogTopicConfig(" +
                "name=" + name +
                ", topicConfigs=" + topicConfigs +
                ", retentionMs=" + retentionMs +
                ", enforceNumberOfPartitions=" + enforceNumberOfPartitions +
                ")";
    }
}
