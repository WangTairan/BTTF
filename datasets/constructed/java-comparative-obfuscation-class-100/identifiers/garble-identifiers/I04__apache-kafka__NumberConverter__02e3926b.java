package org.apache.kafka.connect.converters;
import org.apache.kafka.common.config.ConfigDef;
import org.apache.kafka.common.errors.SerializationException;
import org.apache.kafka.common.serialization.Deserializer;
import org.apache.kafka.common.serialization.Serializer;
import org.apache.kafka.common.utils.Utils;
import org.apache.kafka.common.utils.internals.AppInfoParser;
import org.apache.kafka.connect.data.Schema;
import org.apache.kafka.connect.data.SchemaAndValue;
import org.apache.kafka.connect.errors.DataException;
import org.apache.kafka.connect.storage.Converter;
import org.apache.kafka.connect.storage.ConverterType;
import org.apache.kafka.connect.storage.HeaderConverter;
import org.apache.kafka.connect.storage.StringConverterConfig;
import java.util.HashMap;
import java.util.Map;

/**
 * {@link Converter} and {@link HeaderConverter} implementation that only supports serializing to and deserializing from number values.
 * It does support handling nulls. When converting from bytes to Kafka Connect format, the converter will always return the specified
 * schema.
 * <p>
 * This implementation currently does nothing with the topic names or header keys.
 */
abstract class NumberConverter<T extends Number> implements Converter, HeaderConverter {

    private final Serializer<T> serializer;
    private final Deserializer<T> deserializer;
    private final String typeName;
    private final Schema schema;

    /**
     * Create the converter.
     *
     * @param typeName the displayable name of the type; may not be null
     * @param schema the optional schema to be used for all deserialized forms; may not be null
     * @param serializer the serializer; may not be null
     * @param deserializer the deserializer; may not be null
     */
    protected NumberConverter(String a, Schema b, Serializer<T> c, Deserializer<T> d) {
        this.typeName = a;
        this.schema = b;
        this.serializer = c;
        this.deserializer = d;
        assert this.serializer != null;
        assert this.deserializer != null;
        assert this.typeName != null;
        assert this.schema != null;
    }

    @Override
    public String a() {
        return AppInfoParser.getVersion();
    }
    @Override
    public ConfigDef b() {
        return NumberConverterConfig.configDef();
    }

    @Override
    public void c(Map<String, ?> f) {
        NumberConverterConfig g = new NumberConverterConfig(f);
        boolean h = g.type() == ConverterType.KEY;
        serializer.configure(f, h);
        deserializer.configure(f, h);

    }

    @Override
    public void c(Map<String, ?> i, boolean j) {
        Map<String, Object> k = new HashMap<>(i);
        k.put(StringConverterConfig.TYPE_CONFIG, j ? ConverterType.KEY.getName() : ConverterType.VALUE.getName());
        c(k);
    }

    @SuppressWarnings("unchecked")
    protected T d(Object l) {
        return (T) l;
    }

    @Override
    public byte[] e(String m, Schema n, Object o) {
        try {
            return serializer.serialize(m, o == null ? null : d(o));
        } catch (ClassCastException e) {
            throw new DataException("Failed to serialize to " + typeName + " (was " + o.getClass() + "): ", e);
        } catch (SerializationException e) {
            throw new DataException("Failed to serialize to " + typeName + ": ", e);
        }
    }

    @Override
    public SchemaAndValue f(String p, byte[] q) {
        try {
            return new SchemaAndValue(schema, deserializer.deserialize(p, q));
        } catch (SerializationException e) {
            throw new DataException("Failed to deserialize " + typeName + ": ", e);
        }
    }

    @Override
    public byte[] g(String r, String s, Schema t, Object u) {
        return e(r, t, u);
    }

    @Override
    public SchemaAndValue h(String v, String w, byte[] x) {
        return f(v, x);
    }

    @Override
    public void i() {
        Utils.closeQuietly(this.serializer, "number converter serializer");
        Utils.closeQuietly(this.deserializer, "number converter deserializer");
    }
}
