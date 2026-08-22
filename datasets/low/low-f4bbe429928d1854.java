package org.apache.ibatis.reflection.factory;
import java.io.Serializable;
import java.lang.reflect.Constructor;
import java.util.ArrayList;
import java.util.Collection;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Properties;
import java.util.Set;
import java.util.SortedSet;
import java.util.TreeSet;
import org.apache.ibatis.reflection.ReflectionException;
import org.apache.ibatis.reflection.factory.ObjectFactory;

public class DefaultObjectFactory
implements ObjectFactory,
Serializable {
    private static final long serialVersionUID = -8855120656740914948L;

    @Override
    public <T> T create(Class<T> type) {
        return this.create(type, null, null);
    }

    @Override
    public <T> T create(Class<T> type, List<Class<?>> constructorArgTypes, List<Object> constructorArgs) {
        Class<?> classToCreate = this.resolveInterface(type);
        return (T)this.instantiateClass(classToCreate, constructorArgTypes, constructorArgs);
    }

    @Override
    public void setProperties(Properties properties) {
    }

    <T> T instantiateClass(Class<T> type, List<Class<?>> constructorArgTypes, List<Object> constructorArgs) {
        try {
            if (constructorArgTypes == null || constructorArgs == null) {
                Constructor<T> constructor = type.getDeclaredConstructor(new Class[0]);
                if (!constructor.isAccessible()) {
                    constructor.setAccessible(true);
                }
                return constructor.newInstance(new Object[0]);
            }
            Constructor<T> constructor = type.getDeclaredConstructor(constructorArgTypes.toArray(new Class[constructorArgTypes.size()]));
            if (!constructor.isAccessible()) {
                constructor.setAccessible(true);
            }
            return constructor.newInstance(constructorArgs.toArray(new Object[constructorArgs.size()]));
        }
        catch (Exception e) {
            StringBuilder argTypes = new StringBuilder();
            if (constructorArgTypes != null && !constructorArgTypes.isEmpty()) {
                for (Class<?> argType : constructorArgTypes) {
                    argTypes.append(argType.getSimpleName());
                    argTypes.append(",");
                }
                argTypes.deleteCharAt(argTypes.length() - 1);
            }
            StringBuilder argValues = new StringBuilder();
            if (constructorArgs != null && !constructorArgs.isEmpty()) {
                for (Object argValue : constructorArgs) {
                    argValues.append(String.valueOf(argValue));
                    argValues.append(",");
                }
                argValues.deleteCharAt(argValues.length() - 1);
            }
            throw new ReflectionException("Error instantiating " + type + " with invalid types (" + argTypes + ") or values (" + argValues + "). Cause: " + e, e);
        }
    }

    protected Class<?> resolveInterface(Class<?> type) {
        Class classToCreate = type == List.class || type == Collection.class || type == Iterable.class ? ArrayList.class : (type == Map.class ? HashMap.class : (type == SortedSet.class ? TreeSet.class : (type == Set.class ? HashSet.class : type)));
        return classToCreate;
    }

    @Override
    public <T> boolean isCollection(Class<T> type) {
        return Collection.class.isAssignableFrom(type);
    }
}
