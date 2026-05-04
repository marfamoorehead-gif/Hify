import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Form, Input, Select, Button, Typography } from "antd";
import { useMutation } from "@tanstack/react-query";
import { createApp } from "@/services/app";
import type { AppCreateRequest } from "@/types/app";
import { APP_TYPE_LABELS } from "@/utils/constants";

const { Title } = Typography;

export default function AppCreate() {
  const navigate = useNavigate();
  const [submitting, setSubmitting] = useState(false);
  const [form] = Form.useForm<AppCreateRequest>();

  const mutation = useMutation({
    mutationFn: createApp,
    onSuccess: () => navigate("/apps"),
  });

  const onFinish = async (values: AppCreateRequest) => {
    setSubmitting(true);
    try {
      await mutation.mutateAsync(values);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ maxWidth: 600 }}>
      <Title level={3}>创建应用</Title>
      <Form form={form} layout="vertical" onFinish={onFinish}>
        <Form.Item
          name="name"
          label="应用名称"
          rules={[
            { required: true, message: "请输入应用名称" },
            { max: 100, message: "名称不超过 100 个字符" },
          ]}
        >
          <Input placeholder="输入应用名称" />
        </Form.Item>

        <Form.Item name="description" label="描述">
          <Input.TextArea rows={3} placeholder="输入应用描述（可选）" />
        </Form.Item>

        <Form.Item
          name="type"
          label="应用类型"
          rules={[{ required: true, message: "请选择应用类型" }]}
        >
          <Select placeholder="选择应用类型">
            {Object.entries(APP_TYPE_LABELS).map(([value, label]) => (
              <Select.Option key={value} value={value}>
                {label}
              </Select.Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item
          name="model_provider_id"
          label="模型提供商"
          rules={[{ required: true, message: "请选择模型提供商" }]}
        >
          <Select placeholder="选择模型提供商" />
        </Form.Item>

        <Form.Item
          name="model_name"
          label="模型名称"
          rules={[{ required: true, message: "请输入模型名称" }]}
        >
          <Input placeholder="如 glm-4、deepseek-chat" />
        </Form.Item>

        <Form.Item>
          <Button type="primary" htmlType="submit" loading={submitting}>
            创建
          </Button>
          <Button style={{ marginLeft: 8 }} onClick={() => navigate("/apps")}>
            取消
          </Button>
        </Form.Item>
      </Form>
    </div>
  );
}
