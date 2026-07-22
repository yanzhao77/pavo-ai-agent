const FEATURES = [
  { icon: '🧠', title: '故事导演', desc: '分析故事结构，制定创作计划' },
  { icon: '🎭', title: '角色设计师', desc: '创造人物形象与性格特征' },
  { icon: '🌆', title: '场景构建师', desc: '设计环境氛围与光影色调' },
  { icon: '🎬', title: '分镜导演', desc: '将故事转化为视觉镜头语言' },
];

export function FeatureSection() {
  return (
    <section className="py-24 px-4 border-t border-white/5">
      <div className="max-w-6xl mx-auto">
        <h2 className="text-2xl font-bold text-white text-center mb-12">
          Your AI Production Team
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {FEATURES.map((f, i) => (
            <div
              key={i}
              className="group p-6 rounded-xl border border-white/10 bg-white/[0.02] hover:bg-white/[0.05] hover:border-white/20 transition-all duration-200 hover:-translate-y-0.5"
            >
              <span className="text-3xl block mb-3">{f.icon}</span>
              <h3 className="text-white font-semibold text-sm">{f.title}</h3>
              <p className="text-gray-500 text-xs mt-1">{f.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
