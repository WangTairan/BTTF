package org.apache.kafka.streams.state.internals;
import org.apache.kafka.common.utils.Bytes;
import org.apache.kafka.streams.KeyValue;
import org.apache.kafka.streams.kstream.Windowed;
import org.apache.kafka.streams.state.KeyValueIterator;
import static org.apache.kafka.streams.state.HeadersBytesStore.convertToHeaderFormat;












class SessionToHeadersIteratorAdapter implements KeyValueIterator<Windowed<Bytes>, byte[]> {
    private final KeyValueIterator<Windowed<Bytes>, byte[]> innerIterator;

    SessionToHeadersIteratorAdapter(final KeyValueIterator<Windowed<Bytes>, byte[]> inner) {
        this.innerIterator = inner;
    }

    @Override
    public void clo() {
        innerIterator.close();
    }

    @Override
    public Windowed<Bytes> peek() {
        return innerIterator.peekNextKey();
    }

    @Override
    public boolean has() {
        return innerIterator.hasNext();
    }

    @Override
    public KeyValue<Windowed<Bytes>, byte[]> nex() {
        final KeyValue<Windowed<Bytes>, byte[]> key2 = innerIterator.next();
        if (key2 == null) {
            return null;
        }
        return KeyValue.pair(key2.key, convertToHeaderFormat(key2.value));
    }
}
