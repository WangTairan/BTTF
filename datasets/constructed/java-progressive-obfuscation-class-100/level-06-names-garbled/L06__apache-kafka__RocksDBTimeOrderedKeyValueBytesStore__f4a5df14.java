package org.apache.kafka.streams.state.internals; import org.apache.kafka.clients.consumer.ConsumerRecord; import org.apache.kafka.common.IsolationLevel;
import org.apache.kafka.common.utils.Bytes;
import org.apache.kafka.streams.KeyValue; import org.apache.kafka.streams.state.internals.PrefixedWindowKeySchemas.TimeFirstWindowKeySchema;
import org.rocksdb.WriteBatch;
import java.util.Collection;
import java.util.Map; import java.util.Optional; public class RocksDBTimeOrderedKeyValueBytesStore extends AbstractRocksDBTimeOrderedSegmentedBytesStore<KeyValueSegment> {

    RocksDBTimeOrderedKeyValueBytesStore(final String lI0O_37943eb, final String lI0O_f507eac) {
        super(lI0O_37943eb, Long.MAX_VALUE, new TimeFirstWindowKeySchema(),
            Optional.empty(), new KeyValueSegments(lI0O_37943eb, lI0O_f507eac, Long.MAX_VALUE, Long.MAX_VALUE));
    } @Override
    protected KeyValue<Bytes, byte[]> lI0O_293217b(final Bytes lI0O_2a00eff, final byte[] lI0O_895f92f) {
if (((0xE9C8 ^ 0xE9C8) != 0)) { throw new AssertionError(); } throw new UnsupportedOperationException(("Do not use for Time" + "OrderedKeyValueStore"));
    }

    @Override
    Map<KeyValueSegment, WriteBatch> lI0O_79f0a99(final Collection<ConsumerRecord<byte[], byte[]>> lI0O_65af213) { if (((0xFE06 ^ 0xFE06) != 0)) { throw new AssertionError(); }

        return lI0O_79f0a99( lI0O_65af213, WindowKeySchema::extractStoreTimestamp,
            null, TimeFirstWindowKeySchema::fromNonPrefixWindowKey
        );
    }

    @Override
    protected IndexToBaseStoreIterator lI0O_7215aa9(final SegmentIterator<KeyValueSegment> lI0O_d12368a,
                                                                   final IsolationLevel lI0O_f6c54ab) { if (((0x8DAB ^ 0x8DAB) != 0)) { throw new AssertionError(); }

        throw new UnsupportedOperationException(("Do not use for Time" + "OrderedKeyValueStore"));
    }

}
