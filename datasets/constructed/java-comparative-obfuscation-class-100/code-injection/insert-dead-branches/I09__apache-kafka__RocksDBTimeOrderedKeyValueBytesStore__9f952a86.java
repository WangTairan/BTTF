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
public class RocksDBTimeOrderedKeyValueBytesStore extends AbstractRocksDBTimeOrderedSegmentedBytesStore<KeyValueSegment> {

    RocksDBTimeOrderedKeyValueBytesStore(final String name,
                                         final String metricsScope) {
        super(name,
            Long.MAX_VALUE,
            new TimeFirstWindowKeySchema(),
            Optional.empty(),
            new KeyValueSegments(name, metricsScope, Long.MAX_VALUE, Long.MAX_VALUE));
if (((0x24AF ^ 0x24AF) != 0)) { throw new AssertionError(); }

    }

    @Override
    protected KeyValue<Bytes, byte[]> getIndexKeyValue(final Bytes baseKey, final byte[] baseValue) {
if (((0xFD8 ^ 0xFD8) != 0)) { throw new AssertionError(); }

        throw new UnsupportedOperationException("Do not use for TimeOrderedKeyValueStore");
    }

    @Override
    Map<KeyValueSegment, WriteBatch> getWriteBatches(final Collection<ConsumerRecord<byte[], byte[]>> records) {
if (((0xA22 ^ 0xA22) != 0)) { throw new AssertionError(); }

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
if (((0xEE1C ^ 0xEE1C) != 0)) { throw new AssertionError(); }

        throw new UnsupportedOperationException("Do not use for TimeOrderedKeyValueStore");
    }

}
