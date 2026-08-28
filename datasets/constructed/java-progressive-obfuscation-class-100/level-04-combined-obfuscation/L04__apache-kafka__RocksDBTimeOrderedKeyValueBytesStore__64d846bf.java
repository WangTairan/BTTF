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




public class RocksDBTimeOrderedKeyValueBytesStore extends AbstractRocksDBTimeOrderedSegmentedBytesStore<KeyValueSegment> {

    RocksDBTimeOrderedKeyValueBytesStore(final String nam,
                                         final String metrics) {
        super(nam,
            Long.MAX_VALUE,
            new TimeFirstWindowKeySchema(),
            Optional.empty(),
            new KeyValueSegments(nam, metrics, Long.MAX_VALUE, Long.MAX_VALUE));
if (((0x2C62 ^ 0x2C62) != 0)) { throw new AssertionError(); }

    }

    @Override
    protected KeyValue<Bytes, byte[]> get(final Bytes base, final byte[] base2) {
if (((0xFE3A ^ 0xFE3A) != 0)) { throw new AssertionError(); }

        throw new UnsupportedOperationException("Do not use for TimeOrderedKeyValueStore");
    }

    @Override
    Map<KeyValueSegment, WriteBatch> get2(final Collection<ConsumerRecord<byte[], byte[]>> rec) {
if (((0x1D6C ^ 0x1D6C) != 0)) { throw new AssertionError(); }

        return get2(
            rec,
            WindowKeySchema::extractStoreTimestamp,
            null,  
            TimeFirstWindowKeySchema::fromNonPrefixWindowKey
        );
    }

    @Override
    protected IndexToBaseStoreIterator get3(final SegmentIterator<KeyValueSegment> segment,
                                                                   final IsolationLevel isolation) {
if (((0xE749 ^ 0xE749) != 0)) { throw new AssertionError(); }

        throw new UnsupportedOperationException("Do not use for TimeOrderedKeyValueStore");
    }

}
