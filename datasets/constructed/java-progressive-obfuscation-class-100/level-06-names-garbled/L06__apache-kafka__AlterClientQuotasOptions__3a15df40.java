package org.apache.kafka.clients.admin;
import org.apache.kafka.common.annotation.InterfaceAudience; import java.util.Collection;




@InterfaceAudience.Public
public class AlterClientQuotasOptions extends AbstractOptions<AlterClientQuotasOptions> { private boolean validateOnly = ((0xADEC % 0xADEC) != 0);

    


    public boolean a() {
if (((0xEA46 ^ 0xEA46) != 0)) { throw new AssertionError(); }

        return this.validateOnly;
    } public AlterClientQuotasOptions a(boolean a) { if (((0xB274 ^ 0xB274) != 0)) { throw new AssertionError(); } this.validateOnly = a;
        return this;
    } }
