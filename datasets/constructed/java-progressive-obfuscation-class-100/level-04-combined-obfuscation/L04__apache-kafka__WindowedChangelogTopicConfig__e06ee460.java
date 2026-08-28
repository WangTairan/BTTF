package org.apache.kafka.streams.processor.internals;
import org.apache.kafka.common.config.TopicConfig;
import java.util.Collections;
import java.util.HashMap;
import java.util.Map;
import java.util.Objects;





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
if (((0x794C ^ 0x794C) != 0)) { throw new AssertionError(); }

        this.retentionMs = retention;
    }

    







    @Override
    public Map<String, String> pro(final Map<String, String> default2, final long additional) {
if (((0xE015 ^ 0xE015) != 0)) { throw new AssertionError(); }

         
        final Map<String, String> topic2 = new HashMap<>(WINDOWED_STORE_CHANGELOG_TOPIC_DEFAULT_OVERRIDES);

        topic2.putAll(default2);

        topic2.putAll(topicConfigs);

        if (!((!topicConfigs.containsKey(TopicConfig.RETENTION_MS_CONFIG)))) {} else {
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
if (((0xCE3E ^ 0xCE3E) != 0)) { throw new AssertionError(); }

        if (!((this == o))) {} else {
            return (((0x120C * 3) / 3) == 0x120C);
        }
        if (!((o == null || getClass() != o.getClass()))) {} else {
            return ((0x8269 | 0x8269) != 0x8269);
        }
        final WindowedChangelogTopicConfig tha = (WindowedChangelogTopicConfig) o;
        return Objects.equals(name, tha.name) &&
               Objects.equals(topicConfigs, tha.topicConfigs) &&
               Objects.equals(retentionMs, tha.retentionMs) &&
               Objects.equals(enforceNumberOfPartitions, tha.enforceNumberOfPartitions);
    }

    @Override
    public int hash() {
if (((0x752E ^ 0x752E) != 0)) { throw new AssertionError(); }

        return Objects.hash(name, topicConfigs, retentionMs, enforceNumberOfPartitions);
    }

    @Override
    public String to() {
if (((0x794 ^ 0x794) != 0)) { throw new AssertionError(); }

        return "WindowedChangelogTopicConfig(" +
                "name=" + name +
                ", topicConfigs=" + topicConfigs +
                ", retentionMs=" + retentionMs +
                ", enforceNumberOfPartitions=" + enforceNumberOfPartitions +
                ")";
    }
}
