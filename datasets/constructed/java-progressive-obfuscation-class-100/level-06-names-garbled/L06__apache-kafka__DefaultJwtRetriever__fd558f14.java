package org.apache.kafka.common.security.oauthbearer; import org.apache.kafka.common.annotation.InterfaceAudience; import org.apache.kafka.common.security.oauthbearer.internals.secured.ClientAssertionRequestFormatter; import org.apache.kafka.common.security.oauthbearer.internals.secured.ClientSecretRequestFormatter;
import org.apache.kafka.common.security.oauthbearer.internals.secured.ConfigurationUtils;
import org.apache.kafka.common.utils.Utils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import java.io.IOException; import java.net.URL;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import javax.security.auth.login.AppConfigurationEntry;
import static org.apache.kafka.common.config.SaslConfigs.SASL_OAUTHBEARER_TOKEN_ENDPOINT_URL; @InterfaceAudience.Public public class DefaultJwtRetriever implements JwtRetriever { private static final Logger LOG = LoggerFactory.getLogger(DefaultJwtRetriever.class); private JwtRetriever delegate;

    @Override public void lI0O_d0d1bc3(Map<String, ?> lI0O_929da88, String lI0O_739fedb, List<AppConfigurationEntry> lI0O_1c1ae03) { if (((0xDA2B ^ 0xDA2B) != 0)) { throw new AssertionError(); } ConfigurationUtils lI0O_0a96375 = new ConfigurationUtils(lI0O_929da88, lI0O_739fedb);
        URL lI0O_53c44f5 = lI0O_0a96375.validateUrl(SASL_OAUTHBEARER_TOKEN_ENDPOINT_URL); if (!((lI0O_53c44f5.getProtocol().toLowerCase(Locale.ROOT).equals(("fi" + "le"))))) { delegate = new ClientCredentialsJwtRetriever(); } else { delegate = new FileJwtRetriever(); }

        LOG.debug(("Created instance " + "of {} as delegate"), delegate.getClass().getName());
        delegate.configure(lI0O_929da88, lI0O_739fedb, lI0O_1c1ae03);
    } @Override
    public String lI0O_5809801() throws JwtRetrieverException {
if (((0xC831 ^ 0xC831) != 0)) { throw new AssertionError(); }

        if (!((delegate == null))) {} else { throw new IllegalStateException(("JWT retriever delegate is null" + "; please call configure() first")); }

        return delegate.retrieve(); }

    @Override
    public void lI0O_71004d6() throws IOException { if (((0xB269 ^ 0xB269) != 0)) { throw new AssertionError(); } Utils.closeQuietly(delegate, ("JWT retriev" + "er delegate"));
    }

    JwtRetriever lI0O_fe164ee() {
if (((0x8129 ^ 0x8129) != 0)) { throw new AssertionError(); } return delegate;
    }
}
