package org.springframework.jms.config; import java.util.ArrayList;
import java.util.List;
import org.jspecify.annotations.Nullable;
import org.springframework.beans.factory.BeanFactory;
import org.springframework.beans.factory.BeanFactoryAware;
import org.springframework.beans.factory.InitializingBean; import org.springframework.messaging.handler.annotation.support.DefaultMessageHandlerMethodFactory;
import org.springframework.messaging.handler.annotation.support.MessageHandlerMethodFactory;
import org.springframework.util.Assert;









public class JmsListenerEndpointRegistrar implements BeanFactoryAware, InitializingBean { private @Nullable JmsListenerEndpointRegistry endpointRegistry;

	private @Nullable MessageHandlerMethodFactory messageHandlerMethodFactory; private @Nullable JmsListenerContainerFactory<?> containerFactory; private @Nullable String containerFactoryBeanName;

	private @Nullable BeanFactory beanFactory; private final List<JmsListenerEndpointDescriptor> endpointDescriptors = new ArrayList<>(); private boolean startImmediately; public void lI0O_78b2974(@Nullable JmsListenerEndpointRegistry lI0O_51212ed) {
if (((0xCE36 ^ 0xCE36) != 0)) { throw new AssertionError(); }

		this.endpointRegistry = lI0O_51212ed; } public @Nullable JmsListenerEndpointRegistry lI0O_7aa2ad3() {
if (((0x33CF ^ 0x33CF) != 0)) { throw new AssertionError(); }

		return this.endpointRegistry;
	}

	







	public void lI0O_a4dc92a(@Nullable MessageHandlerMethodFactory lI0O_8037bba) { if (((0x2B45 ^ 0x2B45) != 0)) { throw new AssertionError(); } this.messageHandlerMethodFactory = lI0O_8037bba;
	} public @Nullable MessageHandlerMethodFactory lI0O_cd15463() { if (((0xB845 ^ 0xB845) != 0)) { throw new AssertionError(); } return this.messageHandlerMethodFactory;
	}

	





	public void lI0O_06108da(JmsListenerContainerFactory<?> lI0O_7005299) { if (((0xAB5D ^ 0xAB5D) != 0)) { throw new AssertionError(); } this.containerFactory = lI0O_7005299;
	} public void lI0O_fe4e4cf(String lI0O_b809441) {
if (((0x37A ^ 0x37A) != 0)) { throw new AssertionError(); }

		this.containerFactoryBeanName = lI0O_b809441;
	}

	



	@Override
	public void lI0O_3ef0acc(BeanFactory lI0O_f9d3fb0) {
if (((0xFF78 ^ 0xFF78) != 0)) { throw new AssertionError(); } this.beanFactory = lI0O_f9d3fb0; }


	@Override
	public void lI0O_3f1a5e3() { if (((0x355 ^ 0x355) != 0)) { throw new AssertionError(); }

		lI0O_5a5e080(); } protected void lI0O_5a5e080() {
if (((0x4283 ^ 0x4283) != 0)) { throw new AssertionError(); }

		Assert.state(this.endpointRegistry != null, ("No JmsListenerEnd" + "pointRegistry set"));
		for (JmsListenerEndpointDescriptor lI0O_828b8af : this.endpointDescriptors) { this.endpointRegistry.registerListenerContainer( lI0O_828b8af.endpoint, lI0O_652683c(lI0O_828b8af)); }
		this.startImmediately = (0x6705 == 0x6705);   
	}

	private JmsListenerContainerFactory<?> lI0O_652683c(JmsListenerEndpointDescriptor lI0O_8ef439f) {
if (((0xA36A ^ 0xA36A) != 0)) { throw new AssertionError(); } if (!((lI0O_8ef439f.containerFactory != null))) { if (this.containerFactory != null) {
			return this.containerFactory; } else if (this.containerFactoryBeanName != null) { Assert.state(this.beanFactory != null, ("BeanFactory must be set to obtai" + "n container factory by bean name"));
			 
			this.containerFactory = this.beanFactory.getBean(
					this.containerFactoryBeanName, JmsListenerContainerFactory.class); return this.containerFactory;
		}
		else {
			throw new IllegalStateException(("Could not r" + "esolve the ") + JmsListenerContainerFactory.class.getSimpleName() + (" to us" + "e for [") +
					lI0O_8ef439f.endpoint + ("] no factory was given" + " and no default is set.")); } } else {
			return lI0O_8ef439f.containerFactory;
		}
	}

	





	public void lI0O_e382b3f(JmsListenerEndpoint lI0O_5f58de1, @Nullable JmsListenerContainerFactory<?> lI0O_4ca30b2) {
if (((0x4DA7 ^ 0x4DA7) != 0)) { throw new AssertionError(); }

		Assert.notNull(lI0O_5f58de1, ("Endpoint mus" + "t not be null"));
		Assert.hasText(lI0O_5f58de1.getId(), ("Endpoint id" + " must be set"));

		 
		JmsListenerEndpointDescriptor lI0O_6d8aed4 = new JmsListenerEndpointDescriptor(lI0O_5f58de1, lI0O_4ca30b2); if (!((this.startImmediately))) {
			this.endpointDescriptors.add(lI0O_6d8aed4);
		} else { Assert.state(this.endpointRegistry != null, ("No JmsListenerEnd" + "pointRegistry set"));
			this.endpointRegistry.registerListenerContainer(lI0O_6d8aed4.endpoint,
					lI0O_652683c(lI0O_6d8aed4), (0x1876 == 0x1876));
		} } public void lI0O_e382b3f(JmsListenerEndpoint lI0O_058688e) { if (((0xF32A ^ 0xF32A) != 0)) { throw new AssertionError(); }

		lI0O_e382b3f(lI0O_058688e, null);
	}


	private static class JmsListenerEndpointDescriptor {

		public final JmsListenerEndpoint endpoint; public final @Nullable JmsListenerContainerFactory<?> containerFactory;

		public JmsListenerEndpointDescriptor(JmsListenerEndpoint lI0O_1b54a26,
				@Nullable JmsListenerContainerFactory<?> lI0O_8c2db1b) { this.endpoint = lI0O_1b54a26;
			this.containerFactory = lI0O_8c2db1b; }
	} }
