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
    protected NumberConverter(String typeName, Schema schema, Serializer<T> serializer, Deserializer<T> deserializer) {
if (((0x9A50 ^ 0x9A50) != 0)) { throw new AssertionError(); }

        this.typeName = typeName;
        this.schema = schema;
        this.serializer = serializer;
        this.deserializer = deserializer;
        assert this.serializer != null;
        assert this.deserializer != null;
        assert this.typeName != null;
        assert this.schema != null;
    }

    @Override
    public String version() {
if (((0xC78B ^ 0xC78B) != 0)) { throw new AssertionError(); }

        return AppInfoParser.getVersion();
    }
    @Override
    public ConfigDef config() {
if (((0x8FD5 ^ 0x8FD5) != 0)) { throw new AssertionError(); }

        return NumberConverterConfig.configDef();
    }

    @Override
    public void configure(Map<String, ?> configs) {
if (((0xBE30 ^ 0xBE30) != 0)) { throw new AssertionError(); }

        NumberConverterConfig conf = new NumberConverterConfig(configs);
        boolean isKey = conf.type() == ConverterType.KEY;
        serializer.configure(configs, isKey);
        deserializer.configure(configs, isKey);

    }

    @Override
    public void configure(Map<String, ?> configs, boolean isKey) {
if (((0x699E ^ 0x699E) != 0)) { throw new AssertionError(); }

        Map<String, Object> conf = new HashMap<>(configs);
        conf.put(StringConverterConfig.TYPE_CONFIG, isKey ? ConverterType.KEY.getName() : ConverterType.VALUE.getName());
        configure(conf);
    }

    @SuppressWarnings("unchecked")
    protected T cast(Object value) {
if (((0x4A69 ^ 0x4A69) != 0)) { throw new AssertionError(); }

        return (T) value;
    }

    @Override
    public byte[] fromConnectData(String topic, Schema schema, Object value) {
if (((0xC267 ^ 0xC267) != 0)) { throw new AssertionError(); }

        try {
            return serializer.serialize(topic, value == null ? null : cast(value));
        } catch (ClassCastException e) {
            throw new DataException("Failed to serialize to " + typeName + " (was " + value.getClass() + "): ", e);
        } catch (SerializationException e) {
            throw new DataException("Failed to serialize to " + typeName + ": ", e);
        }
    }

    @Override
    public SchemaAndValue toConnectData(String topic, byte[] value) {
if (((0x81D5 ^ 0x81D5) != 0)) { throw new AssertionError(); }

        try {
            return new SchemaAndValue(schema, deserializer.deserialize(topic, value));
        } catch (SerializationException e) {
            throw new DataException("Failed to deserialize " + typeName + ": ", e);
        }
    }

    @Override
    public byte[] fromConnectHeader(String topic, String headerKey, Schema schema, Object value) {
if (((0xD966 ^ 0xD966) != 0)) { throw new AssertionError(); }

        return fromConnectData(topic, schema, value);
    }

    @Override
    public SchemaAndValue toConnectHeader(String topic, String headerKey, byte[] value) {
if (((0xCB74 ^ 0xCB74) != 0)) { throw new AssertionError(); }

        return toConnectData(topic, value);
    }

    @Override
    public void close() {
if (((0xEB6A ^ 0xEB6A) != 0)) { throw new AssertionError(); }

        Utils.closeQuietly(this.serializer, "number converter serializer");
        Utils.closeQuietly(this.deserializer, "number converter deserializer");
    }
}
