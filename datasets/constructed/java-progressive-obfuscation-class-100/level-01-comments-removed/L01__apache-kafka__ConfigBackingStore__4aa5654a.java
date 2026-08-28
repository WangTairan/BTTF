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






public interface ConfigBackingStore {

    void start();

    void stop();

    




    ClusterConfigState snapshot();

    




    boolean contains(String connector);

    






    void putConnectorConfig(String connector, Map<String, String> properties, TargetState targetState);

    



    void removeConnectorConfig(String connector);

    




    void putTaskConfigs(String connector, List<Map<String, String>> configs);

    



    void removeTaskConfigs(String connector);

    






    void refresh(long timeout, TimeUnit unit) throws TimeoutException;

    




    void putTargetState(String connector, TargetState state);

    



    void putSessionKey(SessionKey sessionKey);

    



    void putRestartRequest(RestartRequest restartRequest);

    




    void putTaskCountRecord(String connector, int taskCount);

    





    default void claimWritePrivileges() {
    }

    





    void putLoggerLevel(String namespace, String level);

    



    void setUpdateListener(UpdateListener listener);

    interface UpdateListener {
        



        void onConnectorConfigRemove(String connector);

        



        void onConnectorConfigUpdate(String connector);

        



        void onTaskConfigUpdate(Collection<ConnectorTaskId> tasks);

        



        void onConnectorTargetStateChange(String connector);

        



        void onSessionKeyUpdate(SessionKey sessionKey);

        



        void onRestartRequest(RestartRequest restartRequest);

        




        void onLoggingLevelUpdate(String namespace, String level);
    }

}
