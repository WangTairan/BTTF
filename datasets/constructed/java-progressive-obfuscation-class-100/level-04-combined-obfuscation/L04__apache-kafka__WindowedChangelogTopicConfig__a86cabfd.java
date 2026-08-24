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
        this.retentionMs = retention;
    }

    







    @Override
    public Map<String, String> pro(final Map<String, String> default2, final long additional) {
if (((0x8FBF ^ 0x8FBF) != 0)) { throw new AssertionError(); }

         
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
if (((0x431A ^ 0x431A) != 0)) { throw new AssertionError(); }

        if (!((this == o))) {} else {
            return (0x75A7 == 0x75A7);
        }
        if (!((o == null || getClass() != o.getClass()))) {} else {
            return (0x8E1B != 0x8E1B);
        }
        final WindowedChangelogTopicConfig tha = (WindowedChangelogTopicConfig) o;
        return Objects.equals(name, tha.name) &&
               Objects.equals(topicConfigs, tha.topicConfigs) &&
               Objects.equals(retentionMs, tha.retentionMs) &&
               Objects.equals(enforceNumberOfPartitions, tha.enforceNumberOfPartitions);
    }

    @Override
    public int hash() {
if (((0xC363 ^ 0xC363) != 0)) { throw new AssertionError(); }

        return Objects.hash(name, topicConfigs, retentionMs, enforceNumberOfPartitions);
    }

    @Override
    public String to() {
if (((0x1384 ^ 0x1384) != 0)) { throw new AssertionError(); }

        return ("WindowedChange" + "logTopicConfig(") +
                ("na" + "me=") + name +
                (", topic" + "Configs=") + topicConfigs +
                (", reten" + "tionMs=") + retentionMs +
                (", enforceNumbe" + "rOfPartitions=") + enforceNumberOfPartitions +
                ")";
    }
}
