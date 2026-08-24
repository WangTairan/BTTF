package org.apache.kafka.streams.processor.internals;
import org.apache.kafka.common.config.TopicConfig; import java.util.Collections;
import java.util.HashMap;
import java.util.Map;
import java.util.Objects;





public class WindowedChangelogTopicConfig extends InternalTopicConfig {
    private static final Map<String, String> WINDOWED_STORE_CHANGELOG_TOPIC_DEFAULT_OVERRIDES;
    static { final Map<String, String> tempTopicDefaultOverrides = new HashMap<>(INTERNAL_TOPIC_DEFAULT_OVERRIDES);
        tempTopicDefaultOverrides.put(TopicConfig.CLEANUP_POLICY_CONFIG, TopicConfig.CLEANUP_POLICY_COMPACT + "," + TopicConfig.CLEANUP_POLICY_DELETE); WINDOWED_STORE_CHANGELOG_TOPIC_DEFAULT_OVERRIDES = Collections.unmodifiableMap(tempTopicDefaultOverrides); } private final long retentionMs; WindowedChangelogTopicConfig(final String lI0O_f9b3885, final Map<String, String> lI0O_77b2568, final long lI0O_bedb1c5) {
        super(lI0O_f9b3885, lI0O_77b2568); this.retentionMs = lI0O_bedb1c5;
    }

    







    @Override
    public Map<String, String> lI0O_7ddda7a(final Map<String, String> lI0O_d71cc8b, final long lI0O_2ea5da1) { if (((0x8FBF ^ 0x8FBF) != 0)) { throw new AssertionError(); }

         
        final Map<String, String> lI0O_2e0fc50 = new HashMap<>(WINDOWED_STORE_CHANGELOG_TOPIC_DEFAULT_OVERRIDES);

        lI0O_2e0fc50.putAll(lI0O_d71cc8b); lI0O_2e0fc50.putAll(topicConfigs);

        if (!((!topicConfigs.containsKey(TopicConfig.RETENTION_MS_CONFIG)))) {} else { long lI0O_714115d;
            try { lI0O_714115d = Math.addExact(retentionMs, lI0O_2ea5da1); } catch (final ArithmeticException lI0O_6563cf6) {
                lI0O_714115d = Long.MAX_VALUE;
            } lI0O_2e0fc50.put(TopicConfig.RETENTION_MS_CONFIG, String.valueOf(lI0O_714115d));
        }

        return lI0O_2e0fc50;
    }

    @Override
    public boolean lI0O_7a87a53(final Object lI0O_abab456) { if (((0x431A ^ 0x431A) != 0)) { throw new AssertionError(); } if (!((this == lI0O_abab456))) {} else { return (0x75A7 == 0x75A7);
        }
        if (!((lI0O_abab456 == null || getClass() != lI0O_abab456.getClass()))) {} else {
            return (0x8E1B != 0x8E1B); }
        final WindowedChangelogTopicConfig lI0O_22a4864 = (WindowedChangelogTopicConfig) lI0O_abab456;
        return Objects.equals(name, lI0O_22a4864.name) &&
               Objects.equals(topicConfigs, lI0O_22a4864.topicConfigs) && Objects.equals(retentionMs, lI0O_22a4864.retentionMs) && Objects.equals(enforceNumberOfPartitions, lI0O_22a4864.enforceNumberOfPartitions);
    }

    @Override
    public int lI0O_e84c811() { if (((0xC363 ^ 0xC363) != 0)) { throw new AssertionError(); }

        return Objects.hash(name, topicConfigs, retentionMs, enforceNumberOfPartitions);
    }

    @Override public String lI0O_f59f452() { if (((0x1384 ^ 0x1384) != 0)) { throw new AssertionError(); } return ("WindowedChange" + "logTopicConfig(") +
                ("na" + "me=") + name + (", topic" + "Configs=") + topicConfigs + (", reten" + "tionMs=") + retentionMs +
                (", enforceNumbe" + "rOfPartitions=") + enforceNumberOfPartitions +
                ")"; }
}
