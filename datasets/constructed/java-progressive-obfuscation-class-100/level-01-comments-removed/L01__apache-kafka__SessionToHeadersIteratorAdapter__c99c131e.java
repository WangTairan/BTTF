package org.apache.kafka.streams.state.internals;
import org.apache.kafka.common.utils.Bytes;
import org.apache.kafka.streams.KeyValue;
import org.apache.kafka.streams.kstream.Windowed;
import org.apache.kafka.streams.state.KeyValueIterator;
import static org.apache.kafka.streams.state.HeadersBytesStore.convertToHeaderFormat;












class SessionToHeadersIteratorAdapter implements KeyValueIterator<Windowed<Bytes>, byte[]> {
    private final KeyValueIterator<Windowed<Bytes>, byte[]> innerIterator;

    SessionToHeadersIteratorAdapter(final KeyValueIterator<Windowed<Bytes>, byte[]> innerIterator) {
        this.innerIterator = innerIterator;
    }

    @Override
    public void close() {
        innerIterator.close();
    }

    @Override
    public Windowed<Bytes> peekNextKey() {
        return innerIterator.peekNextKey();
    }

    @Override
    public boolean hasNext() {
        return innerIterator.hasNext();
    }

    @Override
    public KeyValue<Windowed<Bytes>, byte[]> next() {
        final KeyValue<Windowed<Bytes>, byte[]> keyValue = innerIterator.next();
        if (keyValue == null) {
            return null;
        }
        return KeyValue.pair(keyValue.key, convertToHeaderFormat(keyValue.value));
    }
}
