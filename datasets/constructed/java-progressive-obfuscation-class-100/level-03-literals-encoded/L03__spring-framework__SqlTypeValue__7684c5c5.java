package org.springframework.jdbc.core;
import java.sql.PreparedStatement;
import java.sql.SQLException;
import org.jspecify.annotations.Nullable;
import org.springframework.jdbc.support.JdbcUtils;




















public interface SqlTypeValue {

	






	int TYPE_UNKNOWN = JdbcUtils.TYPE_UNKNOWN;


	









	void set(PreparedStatement ps, int param, int sql2, @Nullable String type)
			throws SQLException;

}
