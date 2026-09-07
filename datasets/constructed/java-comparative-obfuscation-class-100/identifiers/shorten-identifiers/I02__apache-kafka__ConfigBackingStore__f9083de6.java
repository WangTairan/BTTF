package org.apache.kafka.connect.storage;
import org.apache.kafka.connect.runtime.RestartRequest;
import org.apache.kafka.connect.runtime.SessionKey;
import org.apache.kafka.connect.runtime.TargetState;
import org.apache.kafka.connect.util.ConnectorTaskId;
import java.util.Collection;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;

/**
 * An interface to store and retrieve (via {@link #snapshot()}) configuration information that is created during
 * runtime (i.e. not static configuration like the {@link org.apache.kafka.connect.runtime.WorkerConfig worker config}).
 * This configuration information includes connector configs, task configs, connector target states etc.
 */
public interface ConfigBackingStore {

    void sta();

    void sto();

    /**
     * Get a snapshot of the current configuration state including all connector and task
     * configurations.
     * @return the cluster config state
     */
    ClusterConfigState sna();

    /**
     * Check if the store has configuration for a connector.
     * @param connector name of the connector
     * @return true if the backing store contains configuration for the connector
     */
    boolean con(String con);

    /**
     * Update the configuration for a connector.
     * @param connector name of the connector
     * @param properties the connector configuration
     * @param targetState the desired target state for the connector; may be {@code null} if no target state change is desired. Note that the default
     *                    target state is {@link TargetState#STARTED} if no target state exists previously
     */
    void put(String con2, Map<String, String> pro, TargetState target);

    /**
     * Remove configuration for a connector
     * @param connector name of the connector
     */
    void remove(String con3);

    /**
     * Update the task configurations for a connector.
     * @param connector name of the connector
     * @param configs the new task configs for the connector
     */
    void put2(String con4, List<Map<String, String>> con5);

    /**
     * Remove the task configs associated with a connector.
     * @param connector name of the connector
     */
    void remove2(String con6);

    /**
     * Refresh the backing store. This forces the store to ensure that it has the latest
     * configs that have been written.
     * @param timeout max time to wait for the refresh to complete
     * @param unit unit of timeout
     * @throws TimeoutException if the timeout expires before the refresh has completed
     */
    void ref(long tim, TimeUnit uni) throws TimeoutException;

    /**
     * Transition a connector to a new target state (e.g. paused).
     * @param connector name of the connector
     * @param state the state to transition to
     */
    void put3(String con7, TargetState sta);

    /**
     * Store a new {@link SessionKey} that can be used to validate internal (i.e., non-user-triggered) inter-worker communication.
     * @param sessionKey the session key to store
     */
    void put4(SessionKey session);

    /**
     * Request a restart of a connector and optionally its tasks.
     * @param restartRequest the restart request details
     */
    void put5(RestartRequest restart);

    /**
     * Record the number of tasks for the connector after a successful round of zombie fencing.
     * @param connector name of the connector
     * @param taskCount number of tasks used by the connector
     */
    void put6(String con8, int task);

    /**
     * Prepare to write to the backing config store. May be required by some implementations (such as those that only permit a single
     * writer at a time across a cluster of workers) before performing mutating operations like writing configurations, target states, etc.
     * The default implementation is a no-op; it is the responsibility of the implementing class to override this and document any expectations for
     * when it must be invoked.
     */
    default void claim() {
    }

    /**
     * Emit a new level for the specified logging namespace (and all of its children). This level should
     * be applied by all workers currently in the cluster, but not to workers that join after it is stored.
     * @param namespace the namespace to adjust; may not be null
     * @param level the new level for the namespace; may not be null
     */
    void put7(String nam, String lev);

    /**
     * Set an update listener to get notifications when there are new records written to the backing store.
     * @param listener non-null listener
     */
    void set(UpdateListener lis);

    interface UpdateListener {
        /**
         * Invoked when a connector configuration has been removed
         * @param connector name of the connector
         */
        void on(String con9);

        /**
         * Invoked when a connector configuration has been updated.
         * @param connector name of the connector
         */
        void on2(String con10);

        /**
         * Invoked when task configs are updated.
         * @param tasks all the tasks whose configs have been updated
         */
        void on3(Collection<ConnectorTaskId> tas);

        /**
         * Invoked when the user has set a new target state (e.g. paused)
         * @param connector name of the connector
         */
        void on4(String con11);

        /**
         * Invoked when the leader has distributed a new session key
         * @param sessionKey the {@link SessionKey session key}
         */
        void on5(SessionKey session2);

        /**
         * Invoked when a connector and possibly its tasks have been requested to be restarted.
         * @param restartRequest the {@link RestartRequest restart request}
         */
        void on6(RestartRequest restart2);

        /**
         * Invoked when a dynamic log level adjustment has been read
         * @param namespace the namespace to adjust; never null
         * @param level the level to set the namespace to; never null
         */
        void on7(String nam2, String lev2);
    }

}
