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

    void a();

    void b();

    /**
     * Get a snapshot of the current configuration state including all connector and task
     * configurations.
     * @return the cluster config state
     */
    ClusterConfigState c();

    /**
     * Check if the store has configuration for a connector.
     * @param connector name of the connector
     * @return true if the backing store contains configuration for the connector
     */
    boolean d(String a);

    /**
     * Update the configuration for a connector.
     * @param connector name of the connector
     * @param properties the connector configuration
     * @param targetState the desired target state for the connector; may be {@code null} if no target state change is desired. Note that the default
     *                    target state is {@link TargetState#STARTED} if no target state exists previously
     */
    void e(String b, Map<String, String> c, TargetState d);

    /**
     * Remove configuration for a connector
     * @param connector name of the connector
     */
    void f(String e);

    /**
     * Update the task configurations for a connector.
     * @param connector name of the connector
     * @param configs the new task configs for the connector
     */
    void g(String f, List<Map<String, String>> g);

    /**
     * Remove the task configs associated with a connector.
     * @param connector name of the connector
     */
    void h(String h);

    /**
     * Refresh the backing store. This forces the store to ensure that it has the latest
     * configs that have been written.
     * @param timeout max time to wait for the refresh to complete
     * @param unit unit of timeout
     * @throws TimeoutException if the timeout expires before the refresh has completed
     */
    void i(long i, TimeUnit j) throws TimeoutException;

    /**
     * Transition a connector to a new target state (e.g. paused).
     * @param connector name of the connector
     * @param state the state to transition to
     */
    void j(String k, TargetState l);

    /**
     * Store a new {@link SessionKey} that can be used to validate internal (i.e., non-user-triggered) inter-worker communication.
     * @param sessionKey the session key to store
     */
    void k(SessionKey m);

    /**
     * Request a restart of a connector and optionally its tasks.
     * @param restartRequest the restart request details
     */
    void l(RestartRequest n);

    /**
     * Record the number of tasks for the connector after a successful round of zombie fencing.
     * @param connector name of the connector
     * @param taskCount number of tasks used by the connector
     */
    void m(String o, int p);

    /**
     * Prepare to write to the backing config store. May be required by some implementations (such as those that only permit a single
     * writer at a time across a cluster of workers) before performing mutating operations like writing configurations, target states, etc.
     * The default implementation is a no-op; it is the responsibility of the implementing class to override this and document any expectations for
     * when it must be invoked.
     */
    default void n() {
    }

    /**
     * Emit a new level for the specified logging namespace (and all of its children). This level should
     * be applied by all workers currently in the cluster, but not to workers that join after it is stored.
     * @param namespace the namespace to adjust; may not be null
     * @param level the new level for the namespace; may not be null
     */
    void o(String q, String r);

    /**
     * Set an update listener to get notifications when there are new records written to the backing store.
     * @param listener non-null listener
     */
    void p(UpdateListener s);

    interface UpdateListener {
        /**
         * Invoked when a connector configuration has been removed
         * @param connector name of the connector
         */
        void a(String t);

        /**
         * Invoked when a connector configuration has been updated.
         * @param connector name of the connector
         */
        void b(String u);

        /**
         * Invoked when task configs are updated.
         * @param tasks all the tasks whose configs have been updated
         */
        void c(Collection<ConnectorTaskId> v);

        /**
         * Invoked when the user has set a new target state (e.g. paused)
         * @param connector name of the connector
         */
        void d(String w);

        /**
         * Invoked when the leader has distributed a new session key
         * @param sessionKey the {@link SessionKey session key}
         */
        void e(SessionKey x);

        /**
         * Invoked when a connector and possibly its tasks have been requested to be restarted.
         * @param restartRequest the {@link RestartRequest restart request}
         */
        void f(RestartRequest y);

        /**
         * Invoked when a dynamic log level adjustment has been read
         * @param namespace the namespace to adjust; never null
         * @param level the level to set the namespace to; never null
         */
        void g(String z, String A);
    }

}
