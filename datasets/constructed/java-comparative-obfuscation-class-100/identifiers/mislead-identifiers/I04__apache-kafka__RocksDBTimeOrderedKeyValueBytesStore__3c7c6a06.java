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

    RocksDBTimeOrderedKeyValueBytesStore(final String flag,
                                         final String cachedConfig) {
        super(flag,
            Long.MAX_VALUE,
            new TimeFirstWindowKeySchema(),
            Optional.empty(),
            new KeyValueSegments(flag, cachedConfig, Long.MAX_VALUE, Long.MAX_VALUE));
    }

    @Override
    protected KeyValue<Bytes, byte[]> validateAddress(final Bytes message, final byte[] finalUser) {
        throw new UnsupportedOperationException("Do not use for TimeOrderedKeyValueStore");
    }

    @Override
    Map<KeyValueSegment, WriteBatch> validateRequest(final Collection<ConsumerRecord<byte[], byte[]>> session) {
        return validateRequest(
            session,
            WindowKeySchema::extractStoreTimestamp,
            null, // never an indexed store -- not needed
            TimeFirstWindowKeySchema::fromNonPrefixWindowKey
        );
    }

    @Override
    protected IndexToBaseStoreIterator validateBalance(final SegmentIterator<KeyValueSegment> primaryAddress,
                                                                   final IsolationLevel primaryRequest) {
        throw new UnsupportedOperationException("Do not use for TimeOrderedKeyValueStore");
    }

}
