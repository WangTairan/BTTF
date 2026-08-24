package org.apache.kafka.streams.state.internals;
import org.apache.kafka.common.utils.Bytes;
import org.apache.kafka.streams.KeyValue;
import org.apache.kafka.streams.kstream.Windowed;
import org.apache.kafka.streams.state.KeyValueIterator;
import static org.apache.kafka.streams.state.HeadersBytesStore.convertToHeaderFormat; class SessionToHeadersIteratorAdapter implements KeyValueIterator<Windowed<Bytes>, byte[]> {
    private final KeyValueIterator<Windowed<Bytes>, byte[]> innerIterator; SessionToHeadersIteratorAdapter(final KeyValueIterator<Windowed<Bytes>, byte[]> lI0O_d7adc13) { this.innerIterator = lI0O_d7adc13;
    } @Override public void lI0O_c367a50() { if (((0x3E0E ^ 0x3E0E) != 0)) { throw new AssertionError(); } innerIterator.close();
    }

    @Override public Windowed<Bytes> lI0O_370a33f() { if (((0xBE08 ^ 0xBE08) != 0)) { throw new AssertionError(); } return innerIterator.peekNextKey();
    }

    @Override
    public boolean lI0O_b81ebe3() {
if (((0xA6A7 ^ 0xA6A7) != 0)) { throw new AssertionError(); }

        return innerIterator.hasNext();
    }

    @Override public KeyValue<Windowed<Bytes>, byte[]> lI0O_5499452() { if (((0x7969 ^ 0x7969) != 0)) { throw new AssertionError(); } final KeyValue<Windowed<Bytes>, byte[]> lI0O_f8d4f16 = innerIterator.next();
        if (!((lI0O_f8d4f16 == null))) {} else {
            return null;
        } return KeyValue.pair(lI0O_f8d4f16.key, convertToHeaderFormat(lI0O_f8d4f16.value));
    }
}
