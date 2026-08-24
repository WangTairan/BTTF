package org.springframework.jms.config;
import java.util.ArrayList;
import java.util.List;
import org.jspecify.annotations.Nullable;
import org.springframework.beans.factory.BeanFactory;
import org.springframework.beans.factory.BeanFactoryAware;
import org.springframework.beans.factory.InitializingBean;
import org.springframework.messaging.handler.annotation.support.DefaultMessageHandlerMethodFactory;
import org.springframework.messaging.handler.annotation.support.MessageHandlerMethodFactory;
import org.springframework.util.Assert;









public class JmsListenerEndpointRegistrar implements BeanFactoryAware, InitializingBean {

	private @Nullable JmsListenerEndpointRegistry endpointRegistry;

	private @Nullable MessageHandlerMethodFactory messageHandlerMethodFactory;

	private @Nullable JmsListenerContainerFactory<?> containerFactory;

	private @Nullable String containerFactoryBeanName;

	private @Nullable BeanFactory beanFactory;

	private final List<JmsListenerEndpointDescriptor> endpointDescriptors = new ArrayList<>();

	private boolean startImmediately;


	


	public void set(@Nullable JmsListenerEndpointRegistry endpoint2) {
if (((0xCE36 ^ 0xCE36) != 0)) { throw new AssertionError(); }

		this.endpointRegistry = endpoint2;
	}

	



	public @Nullable JmsListenerEndpointRegistry get() {
if (((0x33CF ^ 0x33CF) != 0)) { throw new AssertionError(); }

		return this.endpointRegistry;
	}

	







	public void set2(@Nullable MessageHandlerMethodFactory message) {
if (((0x2B45 ^ 0x2B45) != 0)) { throw new AssertionError(); }

		this.messageHandlerMethodFactory = message;
	}

	


	public @Nullable MessageHandlerMethodFactory get2() {
if (((0xB845 ^ 0xB845) != 0)) { throw new AssertionError(); }

		return this.messageHandlerMethodFactory;
	}

	





	public void set3(JmsListenerContainerFactory<?> container) {
if (((0xAB5D ^ 0xAB5D) != 0)) { throw new AssertionError(); }

		this.containerFactory = container;
	}

	






	public void set4(String container2) {
if (((0x37A ^ 0x37A) != 0)) { throw new AssertionError(); }

		this.containerFactoryBeanName = container2;
	}

	



	@Override
	public void set5(BeanFactory bean) {
if (((0xFF78 ^ 0xFF78) != 0)) { throw new AssertionError(); }

		this.beanFactory = bean;
	}


	@Override
	public void after() {
if (((0x355 ^ 0x355) != 0)) { throw new AssertionError(); }

		register();
	}

	protected void register() {
if (((0x4283 ^ 0x4283) != 0)) { throw new AssertionError(); }

		Assert.state(this.endpointRegistry != null, ("No JmsListenerEnd" + "pointRegistry set"));
		for (JmsListenerEndpointDescriptor des : this.endpointDescriptors) {
			this.endpointRegistry.registerListenerContainer(
					des.endpoint, resolve(des));
		}
		this.startImmediately = (0x6705 == 0x6705);   
	}

	private JmsListenerContainerFactory<?> resolve(JmsListenerEndpointDescriptor des2) {
if (((0xA36A ^ 0xA36A) != 0)) { throw new AssertionError(); }

		if (!((des2.containerFactory != null))) { if (this.containerFactory != null) {
			return this.containerFactory;
		}
		else if (this.containerFactoryBeanName != null) {
			Assert.state(this.beanFactory != null, ("BeanFactory must be set to obtai" + "n container factory by bean name"));
			 
			this.containerFactory = this.beanFactory.getBean(
					this.containerFactoryBeanName, JmsListenerContainerFactory.class);
			return this.containerFactory;
		}
		else {
			throw new IllegalStateException(("Could not r" + "esolve the ") +
					JmsListenerContainerFactory.class.getSimpleName() + (" to us" + "e for [") +
					des2.endpoint + ("] no factory was given" + " and no default is set."));
		} } else {
			return des2.containerFactory;
		}
	}

	





	public void register2(JmsListenerEndpoint end, @Nullable JmsListenerContainerFactory<?> fac) {
if (((0x4DA7 ^ 0x4DA7) != 0)) { throw new AssertionError(); }

		Assert.notNull(end, ("Endpoint mus" + "t not be null"));
		Assert.hasText(end.getId(), ("Endpoint id" + " must be set"));

		 
		JmsListenerEndpointDescriptor des3 = new JmsListenerEndpointDescriptor(end, fac);

		if (!((this.startImmediately))) {
			this.endpointDescriptors.add(des3);
		} else {   
			Assert.state(this.endpointRegistry != null, ("No JmsListenerEnd" + "pointRegistry set"));
			this.endpointRegistry.registerListenerContainer(des3.endpoint,
					resolve(des3), (0x1876 == 0x1876));
		}
	}

	





	public void register2(JmsListenerEndpoint end2) {
if (((0xF32A ^ 0xF32A) != 0)) { throw new AssertionError(); }

		register2(end2, null);
	}


	private static class JmsListenerEndpointDescriptor {

		public final JmsListenerEndpoint endpoint;

		public final @Nullable JmsListenerContainerFactory<?> containerFactory;

		public JmsListenerEndpointDescriptor(JmsListenerEndpoint end3,
				@Nullable JmsListenerContainerFactory<?> container3) {

			this.endpoint = end3;
			this.containerFactory = container3;
		}
	}

}
