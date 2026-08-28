package org.springframework.jdbc.core; import java.sql.PreparedStatement;
import java.sql.SQLException;
import org.jspecify.annotations.Nullable;
import org.springframework.jdbc.support.JdbcUtils;




















public interface SqlTypeValue { int TYPE_UNKNOWN = JdbcUtils.TYPE_UNKNOWN; void a(PreparedStatement a, int b, int c, @Nullable String d)
			throws SQLException;

}
