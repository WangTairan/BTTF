package org.apache.ibatis.cache.decorators;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.locks.ReadWriteLock;
import org.apache.ibatis.cache.Cache;
import org.apache.ibatis.logging.Log;
import org.apache.ibatis.logging.LogFactory;

public class TransactionalCache
implements Cache {
    private static final Log log = LogFactory.getLog(TransactionalCache.class);
    private Cache delegate;
    private boolean clearOnCommit;
    private Map<Object, Object> entriesToAddOnCommit;
    private Set<Object> entriesMissedInCache;

    public TransactionalCache(Cache delegate) {
        this.delegate = delegate;
        this.clearOnCommit = false;
        this.entriesToAddOnCommit = new HashMap<Object, Object>();
        this.entriesMissedInCache = new HashSet<Object>();
    }

    @Override
    public String getId() {
        return this.delegate.getId();
    }

    @Override
    public int getSize() {
        return this.delegate.getSize();
    }

    @Override
    public Object getObject(Object key) {
        Object object = this.delegate.getObject(key);
        if (object == null) {
            this.entriesMissedInCache.add(key);
        }
        if (this.clearOnCommit) {
            return null;
        }
        return object;
    }

    @Override
    public ReadWriteLock getReadWriteLock() {
        return null;
    }

    @Override
    public void putObject(Object key, Object object) {
        this.entriesToAddOnCommit.put(key, object);
    }

    @Override
    public Object removeObject(Object key) {
        return null;
    }

    @Override
    public void clear() {
        this.clearOnCommit = true;
        this.entriesToAddOnCommit.clear();
    }

    public void commit() {
        if (this.clearOnCommit) {
            this.delegate.clear();
        }
        this.flushPendingEntries();
        this.reset();
    }

    public void rollback() {
        this.unlockMissedEntries();
        this.reset();
    }

    private void reset() {
        this.clearOnCommit = false;
        this.entriesToAddOnCommit.clear();
        this.entriesMissedInCache.clear();
    }

    private void flushPendingEntries() {
        for (Map.Entry<Object, Object> entry : this.entriesToAddOnCommit.entrySet()) {
            this.delegate.putObject(entry.getKey(), entry.getValue());
        }
        for (Object object : this.entriesMissedInCache) {
            if (this.entriesToAddOnCommit.containsKey(object)) continue;
            this.delegate.putObject(object, null);
        }
    }

    private void unlockMissedEntries() {
        for (Object entry : this.entriesMissedInCache) {
            try {
                this.delegate.removeObject(entry);
            }
            catch (Exception e) {
                log.warn("Unexpected exception while notifiying a rollback to the cache adapter.Consider upgrading your cache adapter to the latest version.  Cause: " + e);
            }
        }
    }
}
