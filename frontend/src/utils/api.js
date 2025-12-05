// API接口统一管理
const BASE_URL = `http://${window.location.hostname}:8000`;

export const API_ENDPOINTS = {
  RESUME_OPTIMIZATION: `${BASE_URL}/resume_optimization`,
  RESUME_OPTIMIZATION_CHAT: `${BASE_URL}/resume_optimization_chat`,
  GET_RESUME_OPTIMIZATION_RESULT: `${BASE_URL}/get_resume_optimization_result`
};


// 统一的API请求函数 - 针对Form Data格式
export const apiRequest = async (endpoint, data, isFormData = false) => {
  try {
    let requestOptions = {
      method: 'POST',
    };

    if (isFormData) {
      // 对于Form Data格式
      const formData = new FormData();
      Object.keys(data).forEach(key => {
        formData.append(key, data[key]);
      });
      requestOptions.body = formData;
    } else {
      // 对于JSON格式
      requestOptions.headers = {
        'Content-Type': 'application/json',
      };
      requestOptions.body = JSON.stringify(data);
    }

    const response = await fetch(endpoint, requestOptions);

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('API request failed:', error);
    throw error;
  }
};

// 简历优化API
export const resumeOptimizationAPI = async (file, jobData) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('job_name', jobData.job_name || '');
  formData.append('job_description', jobData.job_description || '');
  formData.append('more_info', jobData.more_info || '');
  formData.append('user_request', jobData.user_request || '');

  const response = await fetch(API_ENDPOINTS.RESUME_OPTIMIZATION, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return await response.json();
};

// 简历优化聊天API
export const resumeOptimizationChatAPI = async (chatData) => {
  const formData = new FormData();
  formData.append('history_chat_record', chatData.history_chat_record || '');
  formData.append('user_prompt', chatData.user_prompt || '');
  formData.append('res_opt_record', chatData.res_opt_record || '');

  const response = await fetch(API_ENDPOINTS.RESUME_OPTIMIZATION_CHAT, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return await response.json();
};

// 查询简历优化任务结果API
export const getResumeOptimizationResult = async (taskId) => {
  const formData = new FormData();
  formData.append('task_id', taskId);

  const response = await fetch(API_ENDPOINTS.GET_RESUME_OPTIMIZATION_RESULT, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return await response.json();
};

