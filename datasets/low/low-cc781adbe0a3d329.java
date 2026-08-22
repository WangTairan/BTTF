package org.apache.ibatis.builder.annotation;
import java.lang.reflect.Method;
import java.util.HashMap;
import org.apache.ibatis.builder.BuilderException;
import org.apache.ibatis.builder.SqlSourceBuilder;
import org.apache.ibatis.mapping.BoundSql;
import org.apache.ibatis.mapping.SqlSource;
import org.apache.ibatis.session.Configuration;

/* loaded from: ProviderSqlSource.class */
public class ProviderSqlSource implements SqlSource {
    private SqlSourceBuilder sqlSourceParser;
    private Class<?> providerType;
    private Method providerMethod;
    private boolean providerTakesParameterObject;

    public ProviderSqlSource(Configuration config, Object provider) {
        Method[] methods;
        try {
            this.sqlSourceParser = new SqlSourceBuilder(config);
            this.providerType = (Class) provider.getClass().getMethod("type", new Class[0]).invoke(provider, new Object[0]);
            String providerMethodName = (String) provider.getClass().getMethod("method", new Class[0]).invoke(provider, new Object[0]);
            for (Method m : this.providerType.getMethods()) {
                if (providerMethodName.equals(m.getName()) && m.getParameterTypes().length < 2 && m.getReturnType() == String.class) {
                    this.providerMethod = m;
                    this.providerTakesParameterObject = m.getParameterTypes().length == 1;
                }
            }
            if (this.providerMethod == null) {
                throw new BuilderException("Error creating SqlSource for SqlProvider. Method '" + providerMethodName + "' not found in SqlProvider '" + this.providerType.getName() + "'.");
            }
        } catch (Exception e) {
            throw new BuilderException("Error creating SqlSource for SqlProvider.  Cause: " + e, e);
        }
    }

    @Override // org.apache.ibatis.mapping.SqlSource
    public BoundSql getBoundSql(Object parameterObject) {
        SqlSource sqlSource = createSqlSource(parameterObject);
        return sqlSource.getBoundSql(parameterObject);
    }

    private SqlSource createSqlSource(Object parameterObject) {
        try {
            String sql = this.providerTakesParameterObject ? (String) this.providerMethod.invoke(this.providerType.newInstance(), parameterObject) : (String) this.providerMethod.invoke(this.providerType.newInstance(), new Object[0]);
            Class<?> parameterType = parameterObject == null ? Object.class : parameterObject.getClass();
            return this.sqlSourceParser.parse(sql, parameterType, new HashMap());
        } catch (Exception e) {
            throw new BuilderException("Error invoking SqlProvider method (" + this.providerType.getName() + "." + this.providerMethod.getName() + ").  Cause: " + e, e);
        }
    }
}
