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
 * Sets whether the request should be validated without altering the configs.
 */
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
            null, // we want to truncate the 1 and get 0.
            TimeFirstWindowKeySchema::fromNonPrefixWindowKey
        );
    }

    @Override
    protected IndexToBaseStoreIterator getIndexToBaseStoreIterator(final SegmentIterator<KeyValueSegment> segmentIterator,
                                                                   final IsolationLevel isolationLevel) {
        throw new UnsupportedOperationException("Do not use for TimeOrderedKeyValueStore");
    }

}
