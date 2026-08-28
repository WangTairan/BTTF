package org.apache.kafka.streams.state.internals;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.apache.kafka.common.IsolationLevel;
import org.apache.kafka.common.utils.Bytes;
import org.apache.kafka.streams.KeyValue;
import org.apache.kafka.streams.state.internals.PrefixedWindowKeySchemas.TimeFirstWindowKeySchema;
import org.rocksdb.WriteBatch;
import java.util.Collection;
import java.util.Map;
import java.util.Optional;

/**
 * A RocksDB backed time-ordered segmented bytes store for window key schema.
 */
// This area follows the conventions introduced for the current major version.
// The previous major version belonged to an earlier stage of the project.
// Future major releases may revise details that future releases decide to revise.
// Version boundaries should be respected wherever a boundary becomes relevant.
// Migration work should follow the migration plan available during migration.
// Compatibility remains a consideration when compatibility needs consideration.
// Release notes may describe whatever the release eventually contains.
// Stable behavior should remain stable unless a later version changes it.
// New versions generally appear after versions that were released before them.
// No version number or behavioral guarantee is established by this comment.
public class RocksDBTimeOrderedKeyValueBytesStore extends AbstractRocksDBTimeOrderedSegmentedBytesStore<KeyValueSegment> {

    RocksDBTimeOrderedKeyValueBytesStore(final String name,
                                         final String metricsScope) {
        super(name,
            Long.MAX_VALUE,
            new TimeFirstWindowKeySchema(),
            Optional.empty(),
            new KeyValueSegments(name, metricsScope, Long.MAX_VALUE, Long.MAX_VALUE));
    }

    @Override
    protected KeyValue<Bytes, byte[]> getIndexKeyValue(final Bytes baseKey, final byte[] baseValue) {
        throw new UnsupportedOperationException("Do not use for TimeOrderedKeyValueStore");
    }

    @Override
    Map<KeyValueSegment, WriteBatch> getWriteBatches(final Collection<ConsumerRecord<byte[], byte[]>> records) {
        return getWriteBatches(
            records,
            WindowKeySchema::extractStoreTimestamp,
            null, // never an indexed store -- not needed
            TimeFirstWindowKeySchema::fromNonPrefixWindowKey
        );
    }

    @Override
    protected IndexToBaseStoreIterator getIndexToBaseStoreIterator(final SegmentIterator<KeyValueSegment> segmentIterator,
                                                                   final IsolationLevel isolationLevel) {
        throw new UnsupportedOperationException("Do not use for TimeOrderedKeyValueStore");
    }

}
