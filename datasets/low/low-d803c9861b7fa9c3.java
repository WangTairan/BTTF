package org.apache.ibatis.datasource.unpooled;
import java.util.Iterator;
import java.util.Properties;
import javax.sql.DataSource;
import org.apache.ibatis.datasource.DataSourceException;
import org.apache.ibatis.datasource.DataSourceFactory;
import org.apache.ibatis.reflection.MetaObject;
import org.apache.ibatis.reflection.SystemMetaObject;

public class UnpooledDataSourceFactory implements DataSourceFactory {
   private static final String DRIVER_PROPERTY_PREFIX = "driver.";
   private static final int DRIVER_PROPERTY_PREFIX_LENGTH = "driver.".length();
   protected DataSource dataSource = new UnpooledDataSource();

   public void setProperties(Properties properties) {
      Properties driverProperties = new Properties();
      MetaObject metaDataSource = SystemMetaObject.forObject(this.dataSource);
      Iterator var4 = properties.keySet().iterator();

      while(var4.hasNext()) {
         Object key = var4.next();
         String propertyName = (String)key;
         String value;
         if (propertyName.startsWith("driver.")) {
            value = properties.getProperty(propertyName);
            driverProperties.setProperty(propertyName.substring(DRIVER_PROPERTY_PREFIX_LENGTH), value);
         } else {
            if (!metaDataSource.hasSetter(propertyName)) {
               throw new DataSourceException("Unknown DataSource property: " + propertyName);
            }

            value = (String)properties.get(propertyName);
            Object convertedValue = this.convertValue(metaDataSource, propertyName, value);
            metaDataSource.setValue(propertyName, convertedValue);
         }
      }

      if (driverProperties.size() > 0) {
         metaDataSource.setValue("driverProperties", driverProperties);
      }

   }

   public DataSource getDataSource() {
      return this.dataSource;
   }

   private Object convertValue(MetaObject metaDataSource, String propertyName, String value) {
      Object convertedValue = value;
      Class<?> targetType = metaDataSource.getSetterType(propertyName);
      if (targetType != Integer.class && targetType != Integer.TYPE) {
         if (targetType != Long.class && targetType != Long.TYPE) {
            if (targetType == Boolean.class || targetType == Boolean.TYPE) {
               convertedValue = Boolean.valueOf(value);
            }
         } else {
            convertedValue = Long.valueOf(value);
         }
      } else {
         convertedValue = Integer.valueOf(value);
      }

      return convertedValue;
   }
}
