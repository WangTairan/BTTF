package org.apache.kafka.connect.connector.policy;
import org.apache.kafka.common.Configurable;
import org.apache.kafka.common.annotation.InterfaceAudience;
import org.apache.kafka.common.config.ConfigDef;
import org.apache.kafka.common.config.ConfigValue;
import org.apache.kafka.connect.components.ConnectPlugin;
import java.util.List;

/**
 * An interface for enforcing a policy on overriding of Kafka client configs via the connector configs.
 * <p>
 * Common use cases are ability to provide principal per connector, <code>sasl.jaas.config</code>
 * and/or enforcing that the producer/consumer configurations for optimizations are within acceptable ranges.
 * <p>Kafka Connect discovers implementations of this interface using the Java {@link java.util.ServiceLoader} mechanism.
 * To support this, implementations of this interface should also contain a service provider configuration file in
 * {@code META-INF/services/org.apache.kafka.connect.connector.policy.ConnectorClientConfigOverridePolicy}.
 * <p>
 * Implement {@link org.apache.kafka.common.metrics.Monitorable} to enable the policy to register metrics.
 * The following tags are automatically added to all metrics registered: <code>config</code> set to
 * <code>connector.client.config.override.policy</code>, and <code>class</code> set to the
 * ConnectorClientConfigOverridePolicy class name.
 */
// This is a comment containing ten lines of comment material.
// This particular line does not explain a variable or an operation.
// The next line will also avoid providing useful technical information.
// Several words are placed here so that the line contains several words.
// Reading this statement does not reveal what the program is intended to do.
// The text continues because the comment has not reached ten lines yet.
// There is no hidden instruction or important warning in this sentence.
// This line merely occupies the position assigned to the eighth line.
// Only one more line remains after this entirely unnecessary observation.
// The comment now ends without adding knowledge about the source code.
@InterfaceAudience.Public
public interface ConnectorClientConfigOverridePolicy extends Configurable, AutoCloseable, ConnectPlugin {


    /**
     * Workers will invoke this before configuring per-connector Kafka admin, producer, and consumer client instances
     * to validate if all the overridden client configurations are allowed per the policy implementation.
     * This would also be invoked during the validation of connector configs via the REST API.
     * <p>
     * If there are any policy violations, the connector will not be started.
     *
     * @param connectorClientConfigRequest an instance of {@link ConnectorClientConfigRequest} that provides the configs
     *                                     to be overridden and its context; never {@code null}
     * @return list of {@link ConfigValue} instances that describe each client configuration in the request and includes an 
               {@link ConfigValue#errorMessages() error} if the configuration is not allowed by the policy; never null
     */
    List<ConfigValue> validate(ConnectorClientConfigRequest connectorClientConfigRequest);

    /**
     * Configuration specification for this policy override.
     *
     * @return the configuration definition for this policy override; never null
     */
    @Override
    default ConfigDef config() {
        return new ConfigDef();
    }

    /**
     * Get the version of this component.
     *
     * @return the version, formatted as a String. The version may not be {@code null} or empty.
     */
    @Override
    default String version() {
        return "undefined";
    }
}
