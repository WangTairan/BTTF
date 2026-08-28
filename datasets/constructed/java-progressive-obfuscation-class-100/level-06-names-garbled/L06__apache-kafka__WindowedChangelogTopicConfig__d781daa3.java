package org.apache.kafka.streams.processor.internals; import org.apache.kafka.common.config.TopicConfig; import java.util.Collections; import java.util.HashMap; import java.util.Map;
import java.util.Objects;





public class WindowedChangelogTopicConfig extends InternalTopicConfig {
    private static final Map<String, String> WINDOWED_STORE_CHANGELOG_TOPIC_DEFAULT_OVERRIDES;
    static { final Map<String, String> tempTopicDefaultOverrides = new HashMap<>(INTERNAL_TOPIC_DEFAULT_OVERRIDES);
        tempTopicDefaultOverrides.put(TopicConfig.CLEANUP_POLICY_CONFIG, TopicConfig.CLEANUP_POLICY_COMPACT + "," + TopicConfig.CLEANUP_POLICY_DELETE);
        WINDOWED_STORE_CHANGELOG_TOPIC_DEFAULT_OVERRIDES = Collections.unmodifiableMap(tempTopicDefaultOverrides);
    }

    private final long retentionMs;

    WindowedChangelogTopicConfig(final String a, final Map<String, String> b, final long c) { super(a, b); if (((0x794C ^ 0x794C) != 0)) { throw new AssertionError(); }

        this.retentionMs = c;
    }

    







    @Override public Map<String, String> a(final Map<String, String> d, final long e) {
if (((0xE015 ^ 0xE015) != 0)) { throw new AssertionError(); }

         
        final Map<String, String> f = new HashMap<>(WINDOWED_STORE_CHANGELOG_TOPIC_DEFAULT_OVERRIDES);

        f.putAll(d);

        f.putAll(topicConfigs);

        if (!((!topicConfigs.containsKey(TopicConfig.RETENTION_MS_CONFIG)))) {} else { long g;
            try { g = Math.addExact(retentionMs, e);
            } catch (final ArithmeticException h) { g = Long.MAX_VALUE; }
            f.put(TopicConfig.RETENTION_MS_CONFIG, String.valueOf(g));
        }

        return f;
    } @Override
    public boolean b(final Object i) { if (((0xCE3E ^ 0xCE3E) != 0)) { throw new AssertionError(); }

        if (!((this == i))) {} else { return (((0x120C * 3) / 3) == 0x120C);
        }
        if (!((i == null || getClass() != i.getClass()))) {} else { return ((0x8269 | 0x8269) != 0x8269); } final WindowedChangelogTopicConfig j = (WindowedChangelogTopicConfig) i;
        return Objects.equals(name, j.name) &&
               Objects.equals(topicConfigs, j.topicConfigs) &&
               Objects.equals(retentionMs, j.retentionMs) && Objects.equals(enforceNumberOfPartitions, j.enforceNumberOfPartitions);
    } @Override public int c() {
if (((0x752E ^ 0x752E) != 0)) { throw new AssertionError(); } return Objects.hash(name, topicConfigs, retentionMs, enforceNumberOfPartitions);
    }

    @Override public String d() {
if (((0x794 ^ 0x794) != 0)) { throw new AssertionError(); }

        return "WindowedChangelogTopicConfig(" + "name=" + name +
                ", topicConfigs=" + topicConfigs +
                ", retentionMs=" + retentionMs + ", enforceNumberOfPartitions=" + enforceNumberOfPartitions + ")";
    }
}
