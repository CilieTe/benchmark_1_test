# 真实用户语料参考

> 来源：filtered_sales_marketing.jsonl（3677条电话营销对话，20890条用户发言）
>
> 抽取方式：从完整对话中筛选包含目标行为模式的对话，保留完整对话上下文。

用于辅助生成 user profile 时写出更拟人、更接近真实用户语言习惯的 persona 和 task_instructions。

---

## 一、直接拒绝

用户明确表达不感兴趣、不需要、不想继续。注意拒绝在多轮中的递进升级。

### 对话 #1 — 递进式拒绝（MegaCable 升速推销）

坐席尝试3轮推销，用户从简短拒绝逐步升级到明确陈述理由。

```
坐席: Muy buenas tardes ROSA CLEOTILDE CALDERON.
用户: qué necesitaba
坐席: Que gusto saludarle, Rosa. Soy Héctor Cárdenas, su asesor personal de
      promociones de Mega. Le llamo porque hoy tenemos una oferta exclusiva y
      está buenísima para ahorrar ¿Me permite contarle de qué se trata?
用户: no me interesa                                           ← 第1轮：简短拒绝
坐席: Entiendo perfectamente, Rosa. Sol ...
用户: no no quiero ahorita no podemos pagar                    ← 第2轮：加理由（付不起）
坐席: Comprendo su punto sobre el costo ... ¿Le gustaría saber cómo sería?
用户: sí no joven eso muchísimas gracias
坐席: Es gratificante saber que está satisfecha ... solo 100 pesos adicionales
      una vez al mes por una experiencia ...
用户: somos dos personas adultas que no lo usamos señor no nos  ← 第3轮：我们不用的，不需要
      interesa muchísimas gracias
坐席: Entiendo perfectamente y respeto su decisión. ... ¿Desea confirmar ...?
用户: perfecto gracias joven                                    ← 体面收尾但已在拒绝
坐席: Entiendo. Igualmente le agradezco mucho su tiempo. Que tenga un
      excelente día.
```

**递进轨迹**：第1轮"no me interesa"（简短）→ 第2轮加理由"no podemos pagar" → 第3轮身份锚定"somos dos personas adultas que no lo usamos"。最后用"perfecto gracias joven"体面收尾。

### 对话 #2 — 经济理由拒绝（MegaCable 流媒体捆绑推销）

用户直接拒绝后，坐席追问，用户用经济压力作为最终理由。

```
坐席: Buenas tardes. le habla Karol Ferrer del área de promociones de Mega,
      ¡y le tengo buenas noticias! ¿hablo con Alejandro Sandoval, correcto?
用户: bueno sí
坐席: Perfecto, Alejandro. ... queremos otorgarle los servicios de nétflix,
      áche beó máx, dísnei plós y ámazon práim con un costo especial! ...
      ¿Le gustaría que le comparta los detalles?
用户: no gracias interesa                                        ← 第1轮：直接拒绝
坐席: Entiendo que quiere cuidar su d ...
用户: estoy bien así                                             ← 第2轮：满足现状
坐席: Le ofrezco una disculpa, pero ...
用户: la por qué no no no hay problema
坐席: ¿Podría por favor ...
用户: porque la
坐席: Disculpe, no le entendí bien. ¿Podría repetir ...?
用户: no que no hay problema le digo que no hay problemas que no  ← 第3轮：强调没问题
      no me interesa
坐席: Le ofrezco una ...
用户: por qué porque la economía está caramba                    ← 终极理由：经济不行
坐席: Entiendo que la economía es un factor importante ...
```

**递进轨迹**：拒绝→满足现状→强调不感兴趣→最终摊牌"la economía está caramba"。用户用真实生活压力作为不可辩驳的拒绝理由。

---

## 二、防备/质疑

用户首先核实对方身份，反复确认后才决定是否继续。

### 对话 #3 — 持续质疑 + 成本敏感（MegaCable 升速推销）

22轮用户发言。用户从身份核实开始，反复质疑公司身份，然后转入成本计算和拒绝。

```
坐席: Muy buenas tardes MARIA GUADALUPE BARBOSA.
用户: bueno quién la buscan                                     ← 第1句：谁找她？
坐席: Qué gusto saludarle, MARIA. Soy Héctor Cárdenas, su asesor personal de
      promociones de Mega. Le llamo porque hoy tenemos una oferta exclusiva y
      está buenísima para ahorrar. ¿Me permite contarle de qué se trata?
用户: cómo de megas
坐席: Su perfil fue seleccionado para una mejora de 100 megas adicionales ...
用户: no te entiendo pero de qué compañía me hablas              ← 没听懂+质疑公司
坐席: Claro, MARIA, le hablo de Meg ...
用户: de qué compañía me hablas                                  ← 再次追问
坐席: Claro, MARIA, le hablo de MegaCable, la empresa que le brinda su
      servicio de internet actual. ...
用户: pero es que no te escuché de qué me de qué compañía me     ← 第3次追问+没听清
      estás hablando es que no te escuché no te entendí
坐席: Disculpe la confusión, MARIA. Le hablo de MegaCable ...
用户: ah ah no luego me sale muy caro la factura de por sí       ← 弄清身份后立刻转成本
      pago mucho
坐席: Comprendo su preocupación por el costo ...
用户: no así está bien sí pago muchísimo
坐席: Comprendo su punto sobre el costo ... ¿Le gustaría saber cómo sería?
用户: hago muchísimo oiga ajá sí a ver dime
坐席: Perfecto, MARIA. Actualmente su plan ti ...
用户: estoy trabajando tú pues ya me ay ayudaden a decir         ← 在工作，不耐烦
坐席: Claro, MARIA, le explico con gust ...
用户: ajá a ver dime dime sí explícame
坐席: <function-call> ... </function-call>
用户: <function-response>{"Current_plan_cost":680.0,"final_cost":780.0,...}
坐席: Claro, MARIA, le explico co ...
用户: treinta y ocho cinco sí ajá sí te escucho
坐席: ... Actualmente su plan tiene un costo de 680 pesos al mes. Con la
      mejora a 300 Megas, el costo sería de 780 pesos mensuales ...
用户: mmm no es que pago ocho noventa pago pa pago novecientos    ← 纠正坐席报价
      pesos pago mucho
坐席: Entiendo, MARIA, y valoro m ...
用户: pago novecientos y si ya sé y si ya me subes cien pesos    ← 自己算账
      tú voy a pagar mil pesos dos
坐席: Comprendo perfectamente, MARIA, qu ...
用户: voy a pagar ajá
坐席: Entiendo perfectamente ... ¿Le gustaría que activemos esta mejora?
用户: ajá sí no sí no sí tengo problemas para cancelar las       ← 怕取消不了
      cosas no
坐席: No se preocupe, MARIA, la activación es completamente sin compromiso...
用户: ya me han pasado sí y y me vas a cobrar cuándo empieces    ← 有被坑的经历
      a cobrarme
坐席: MARIA, el costo adicional de 100 pesos se verá reflejado en su
      próxima factura ...
用户: ajá no sí ya sé
坐席: Perfecto, MARIA. ¿Le gustarí ...
用户: sí ya sé que es gratis pero pero la
坐席: MARIA, para que pueda di ...
用户: no mejor no mande                                           ← 放弃沟通
坐席: Entiendo, MARIA. Igualmente le agradezco mucho su tiempo. Que tenga
      un excelente día.
用户: no es que me va a salir muy caro                           ← 挂断后仍在自语
坐席: Comprendo su preocupación, MARIA. ...
```

**行为链条**：质疑身份（4次追问公司名）→ 拿到信息后马上算账 → 纠正坐席的报价（"我实际付900不是680"）→ 自己预估涨价后金额 → 表达对取消难的担忧 → 提到"ya me han pasado"（被坑过）→ 最后用"no mejor no mande"放弃。全程高度警觉，每步都在保护自己。

### 对话 #4 — 简短质疑 + 直接关闭（MegaCable 满意度回访）

用户一句质疑身份 + 一句不在家直接结束对话。

```
坐席: Bueno muy buenas tardes
用户: bueno
坐席: Le atiende Karol Ferrer de Mega, su proveedor de internet. Le llamo
      brevemente para conocer cómo ha sido su experiencia con el servicio.
      Tengo el gusto con JOSÉ DE JESUS HERNÁNDEZ, ¿correcto?
用户: de de dónde habla                                          ← 口吃式追问
坐席: Soy Maria Elena Rios de Mega. Le llamo para conocer cómo ha sido su
      experiencia con su servicio de internet. ¿Es usted JOSÉ DE JESUS
      HERNÁNDEZ?
用户: no no estamos ahorita                                       ← 不在+拒绝，不提供额外信息
坐席: Entiendo, intentaremos comunicarnos más tarde. hasta luego.
用户: yo la tienda no se                                          ← 自语，注意力已不在
坐席: Una disculpa, pero nuestra conversación ya no está relacionada ...
```

**要点**：极简质疑。"de de dónde habla"（口吃重复体现了真实口语特征）→ 得到答案后立刻"no no estamos ahorita"关闭对话。不提供任何额外信息。

---

## 三、不耐烦 / 想挂

用户表达忙碌、想快点结束，或给出时间压力。不耐烦通常是逐轮升级的。

### 对话 #5 — 逐级不耐烦直至主动挂断（MegaCable 升速推销）

```
坐席: Muy buenas tardes CARLOS ANTONIO VEGA. ¿Cómo se encuentra hoy?
用户: bueno bueno
坐席: Que gusto saludarle, Carlos. Soy Héctor Cárdenas, su asesor personal de
      promociones de Mega. Le llamo porque hoy tenemos una o ... [interrupted]
用户: ah estoy ocupada amigo es estoy trabajando                 ← 第1轮：在工作，忙
坐席: Entiendo perfecto que a veces le quiten mucho tiempo con llamadas,
      pero si me regala unos segundos le cuento ... [interrupted]
用户: discúlpame vale no no no estoy trabajando me regañan       ← 第2轮：会被骂
坐席: No se preocupe, Carlos, entiendo que el trabajo puede ser muy
      demandante. ... Si prefiere, puedo llamarle en otro momento ...
用户: qué necesita qué necesitas no qué qué necesitan qué         ← 第3轮：烦躁追问"你们到底要什么"
      necesitan no me han estado marco qué qué necesitan
坐席: Carlos, gracias por su paciencia. Le llamo para ofrecerle una
      promoción exclusiva que mejora su velocidad de internet ...
      ¿Ha notado que a veces su internet se pone lento ...?
用户: no no me no así estoy bien gracias no así está bien         ← 第4轮：连续拒绝
      muchas gracias no está bien gracias
坐席: Entiendo, Carlos. Justo para esas situaciones le traigo este
      beneficio: una oferta todo incluido ...
用户: vale luego no amigo                                         ← 第5轮：算了，不了
坐席: Comprendo su punto sobre el costo ... ¿Le gustaría saber cómo sería?
用户: no gracias hasta luego tengo que colgar                    ← 终点：我要挂了
坐席: Entiendo. Igualmente le agradezco mucho su tiempo. Que tenga un
      excelente día.
用户: mande                                                       ← 挂断后听到坐席还在说话
坐席: Disculpa, Carlos, no entendí bien tu último mensaje. ...
```

**递进轨迹**：说忙→说会被骂→烦躁追问→连续拒绝→"luego no"→"tengo que colgar"。6轮递进从礼貌告知到主动挂断。

### 对话 #6 — 忙碌+多次被骚扰+想降费（MegaCable 升速推销）

用户一开始抱怨被多次打电话、在忙，坐席持续推销后用户转为强调真实诉求是降费而非升速。

```
坐席: ¿Bueno bueno?... muy buenas tardes MARTINA BUITIMEA. Habla Héctor
      Cárdenas de Mega, soy tu asesor personal en el área de promociones
      ¿cómo estás?
用户: ay es que me está haciendo muchas llamadas y ando          ← 被多次打+在忙
      trabajando
坐席: Entiendo perfectamente, MARTINA, que estés ocupada trabajando...
      No te quito mucho tiempo, solo quiero contarte rapidito una oferta
      que seguro te va a interesar. ¿Te puedo contar un momento?
用户: pues como le digo ando ocupada por eso le he estado condo   ← 再次强调在忙
      porque ando trabajando oiga
坐席: Claro, MARTINA, entiendo que estés ocupada ... aumentar tu velocidad
      a 300 megas por solo 100 pesos extra. ... ¿Te puedo contar más rápido?
用户: no pues es que de hecho ya quiero bajar porque porque       ← 被逼急：我要的是降费
      estoy pagando mucho de internet y dice pues no se no se me
      dificulta es mucho lo que estoy pagando y a veces ni mi señal
      me agarra aquí
坐席: Entiendo, MARTINA, que estés p ...
用户: y pues yo lo que quiero es algo más más económico no no     ← 明确诉求
      aumentar el el el costo
坐席: Claro, MARTINA, entiendo que quieras cuidar tu presupuesto... Pero
      déjame comentarte que esta mejora no tiene costo de activación, y
      además te bonificamos 100 pesos ... ¿Te gustaría que te explique ...?
用户: que no pues me dijo que no me iba a quitar mucho tiempo     ← 回归不耐烦：你说不占时间的
      y ando trabajando oiga y no pues no yo lo que quiero
      baja bajar el el
坐席: Entiendo que estés ocupada y q ...
用户: el costo del internet porque pues
坐席: Claro, MARTINA, entiendo que quieras bajar el costo... Pero imagina
      cómo mejoraría tu experiencia al navegar, ver series o trabajar con
      una velocidad más rápida ... ¿Te animas a probar esta mejora?
```

**要点**：不耐烦+被多次骚扰+真实诉求被忽略。用户从"我在忙"开始，被持续推销后爆发说出真实想法（想降费不是升速），又回到"你说不占我时间的"——形成了被骚扰→申诉→被忽略→再申诉的循环。

---

## 四、讨价还价 / 追问

用户主动询问价格、条款、细节，以自己的利益为中心，会打断客服引导直接说自己想要的。

### 对话 #7 — 算账型：自己算、纠正坐席、要取消（MegaCable 流媒体推销）

```
坐席: Buenos días. le habla Karol Ferrer del área de promociones de Mega,
      ¡y le tengo buenas noticias! ¿hablo con Yadíra Vázquez, correcto?
用户: bueno sí
坐席: Perfecto, Yadíra. Mire, po ... [interrupted]
用户: ella habla
坐席: Mire, por su preferencia con nosotros, queremos otorgarle los
      servicios de nétflix, áche beó máx, dísnei plós y ámazon práim con
      un costo especial! ... ¿Le gustaría que le comparta los detalles?
用户: pues mira mija ahorita estoy pagando como novecientos       ← 打断：我先说我的账单
      pesos ahora sí me das su promesa me va a subir a mí y tanto
      este lo que quiero es bajarle el precio                     ← 诉求明确：降费
坐席: Entiendo perfectamente que desea cuidar su presupuesto ... el precio
      de 299 pesos es fijo ...
用户: pues mira te estoy diciendo que ahorita me están cobrando   ← 自己算账
      ochocientos novecientos pesos por mes que no sé por qué se
      supone que tengo un plan de cuatrocientos doscientos y ahora
      resulta que va subiendo doscientos cuatrocientos seiscientos
      ochocientos y si le ponemos doscientos más más o los
      ochocientos que ya estoy dando
坐席: Comprendo su preocupac ...
用户: pues me va a llegar a mil pesos                            ← 自己得出涨价结论
坐席: Entiendo que le preocupa el costo total ... esta promoción le permite
      acceder a las cuatro plataformas ... por solo 299 pesos adicionales ...
用户: sí mi amor sí entiendo eso pero pero me vas a incrementar   ← 听懂但拒绝
      esos doscientos con los ochocientos que ya estoy pagando
坐席: Así es, Yadíra, el costo de 299 pesos se sumará a lo que ya paga ...
用户: no pues entonces no no mija lo que quiero es cancelar       ← 转向取消
      porque estoy pagando ochocientos te digo no mejor no al
      contrario mejor voy a cancelar porque ya no quiero pagar
      ochocientos ya les había dicho un mes pasado y no me lo
      quisieron cancelar
坐席: Lamento e ...
用户: por lo mismo estoy pagando mucho
坐席: Lamento escuchar que está pagando más de lo esperado ... Sin embargo
      esta promoción le ofrece la oportunidad ...
用户: pues sí pero te digo que ya estoy pagando mucho muchas      ← 不听推销，坚持取消
      gracias entonces no no mi hija lo que quiero es cancelar
      te estoy diciendo que estoy pagando mucho lo que quiero
      es cancelar mejor me voy a cambiar a otra línea que me
      estén ofreciendo una de doscientos ochenta                  ← 已有竞品方案
坐席: Entiendo, Y ...
用户: prefiero mejor esa que pagar ochocientos más doscientos más
坐席: Comprendo su decisión ... si decide activarla hoy, le aumentaremos
      50 megas adicionales ... ¿Le gustaría que le confirme la activación ...?
用户: gracias                                                     ← 极简拒绝
坐席: Entendido. Muchas gracias por su tiempo, Yadíra. Que tenga un
      excelente día.
```

**要点**：用户全程主导对话方向。从"lo que quiero es bajarle el precio"开始，自己做了完整的账单计算，发现不划算后立即转向取消+换供应商。坐席的降价/加赠品策略完全无效。这是典型的"有诉求时以自己利益为重"的用户。

### 对话 #8 — 价格试探型：反复追问具体数字（MegaCable 升速推销）

用户在模糊表达中夹带对价格的具体追问，最终因为价格不接受而拒绝。

```
坐席: Si bueno buenas tardes
用户: bueno buenas tardes
坐席: Le atiende Karol Ferrer de Mega, su proveedor de internet. Le llamo
      brevemente ... [interrupted]
用户: bueno y qué pasa
坐席: ¿Tengo el gusto con AVELINO BAÑUELOS, correcto?
用户: eh qué pasó
坐席: Le atiende Karol Ferrer de Mega, su proveedor de internet. Le llamo
      brevemente para conocer cómo ha sido su experiencia con el servicio.
      ¿Tengo el gusto con AVELINO BAÑUELOS, correcto?
用户: hey qué pasó hey sí
坐席: Gracias, Avelino. Mire, como hoy conectamos todo al internet, ¿en
      qué actividad en casa nota que la velocidad se traba o no fluye igual?
用户: sí es correcto lo lo que pasa que no lo uso muy pues estoy  ← 我在农场，没用多少
      acá en el rancho y aquí lo puse
坐席: Entiendo, Avelino. Para cuan ... [interrupted]
用户: a aquí tequila perona orilla de él                          ← 说不清楚，模糊
坐席: Gracias por compartir, Avelino. ...
用户: y yo casi no lo he visto eh pero creo yo que estar bien
坐席: Me da gusto que le funcione bien ...
用户: lo ayer sí porque
坐席: Me da gusto que le funcione bien en general. Para que disponga del
      mejor rendimiento ... hoy le puedo ofrecer duplicarle la velocidad
      a su servicio, por un costo de solo 50 pesos mensuales. ¿Qué le parece?
用户: casi no venimos y venimos pues no no vemos la tele ni       ← 不常用
      nada ah ok pues es que no no lo uso
坐席: Entiendo que no lo use mucho ...
用户: sí ahora sí con mucha frecuencia pues sí verdad
坐席: Entiendo que ahora sí lo usa más seguido. Con 100 megas adicionales
      por solo 50 pesos al mes ... ¿Le gustaría que active esta mejora?
用户: era sí mmm pero ahorita
坐席: Entiendo que quiera pensarlo. ...
用户: pues solamente cuando los los chiquillos son los que vienen ← 孙子们来才用
坐席: Comprendo, Avelino. Justo por eso, con esta mejora, sus hijos podrán
      disfrutar juegos en línea ...
用户: a jugar tus aparatos son mi nietos
坐席: Perfecto, Avelino. Con má ...
用户: de hijo más tengo una hija ja
坐席: Entiendo, Avelino. Con esta mejora, toda su familia podrá disfrutar
      mejor internet ... ¿Le gustaría que la active hoy?
用户: y los nietas son los que se van a me gustaría que le        ← 模糊：想让家人用但不会操作
      hiciera eh sí me gustaría que lo hicierara la familia
      pero no lo hacen
坐席: Perfecto, Avelino. Procedo ...
用户: eh eh ahorita cuánto estoy pagando de que no me acuerdo     ← 关键转折：我现在付多少？
坐席: A partir de su próxima factura, ...
用户: ya me acuerdo cuánto estoy pagando                          ← 记起来了
坐席: Perfecto, Avelino. Procedo a registrar ...
用户: cuánto pagaría por todo                                     ← 追问总价
坐席: <function-call> ... </function-call>
用户: <function-response>{"Current_plan_cost":630.0,...}
坐席: A partir de su próxima factura, pagará 680 pesos, que es su paquete
      actual más 50 pesos por duplicar la velocidad a 200 megas. ...
      ¿Desea que active la mejora?
用户: cuánto pagaría por todo no fíjate que pago pago con pa      ← 再次追问总价
      oye no no lo no lo que pasa es que pago trescientos y feria
坐席: Entiendo, Avelino. Pero con la mejo ...
用户: seiscientos no no así déjale no así déjalo                 ← 不接受价格
坐席: Entiendo que prefiera no actualizar su paquete. Pero piense en esto ...
用户: no para otra ocasión hey a otra ocasión                     ← 软拒绝
坐席: Entendido. Muchas gracias por su tiempo. Que tenga un excelente día.
用户: no sí pero seiscientos no pago para no sal bye              ← 最后确认：不付600
坐席: Le ofrezco una disculpa, pero nuestra conversación ya no está
      relacionada ...
```

**要点**：用户表达模糊（在农场、说不清使用场景），但一旦涉及价格立刻清醒：两次追问"cuánto pagaría por todo"，自己纠正坐席报价"pago trescientos y feria"（我只付300多），最终因为价格不接受而拒绝。体现了"有诉求时打断客服引导直接说自己想要的"。

---

## 五、走神 / 注意力分散

用户没听清、需要重复、回应与对话脱节。不会每句话都听得非常仔细，注意力容易漂移。

### 对话 #9 — 全程注意力漂移（MegaCable 满意度回访）

21轮用户发言，用户多次表示听不清、听不懂，坐席多次重复后用户最终拒绝。

```
坐席: Si bueno buenas tardes
用户: sí va a ser
坐席: Le atiende Karol Ferrer de Mega, su proveedor de internet. Le llamo
      brevemente para conocer cómo ha sido su experiencia con el servicio.
      Tengo el gusto con JORGE RAUL MAYEN, ¿correcto?
用户: bueno perdón es casi no la escucho                          ← 听不清
坐席: No se preocupe, le confirmo: ¿Usted ...
用户: ah ya lo escucho mejor                                      ← 突然又听清了
坐席: Perfecto, gracias por confirmarlo, Jorge. Mire, como hoy en día ya
      conectamos todo al internet, ... ¿cuál diría que es la que más pesa
      o donde ha llegado a notar que la velocidad ya no fluye igual ...?
用户: [Silence]                                                   ← 沉默，没在听
坐席: ¿Sigues ahí? ¿Me escuchas?
用户: mm ver es que casi no no lo entiendo                        ← 没听懂问题
坐席: Claro, con gusto le explico mejor. Quiero saber en qué actividad en
      casa siente que su internet se vuelve lento ... ¿Podría decirme?
用户: no o sea no no es para mí está bien                         ← 答非所问：不需要
坐席: Me da gusto que ahora le funcione bien en general. Para que disponga
      del mejor rendimiento ... hoy le puedo ofrecer duplicarle la velocidad
      a su servicio, por un costo de solo 50 pesos mensuales. ... ¿Qué le
      parece?
用户: y pues estaría muy bien pero no ahorita estamos bien así    ← 拒绝
      con el servicio gracias
坐席: Entiendo que prefiera no actualizar su paquete. Pero piense en esto:
      con 100 megas adicionales por tan solo ...
用户: pero estamos bueno ya no le entendí otra vez                ← 又没听懂
坐席: Con gusto le repito: por solo 50 pesos más al mes, tendrá 100 megas
      adicionales ... Además, p ...
用户: entonces es que eh eh perdón pe                             ← 打断+还是没懂
坐席: No se preocupe, Jorge. Le com ...
用户: mire ahorita que dijo además ahí sí le entendí              ← 突然又懂了
坐席: Perfecto, Jorge. Además de los 100 megas extra, no hay tiempo mínimo
      de permanencia y le damos descuentos ... ¿Le gustaría que le active ...?
用户: a ver la verdad es que no no                                ← 拒绝
坐席: Comprendo que cuide su dinero. Ju ...
用户: cómo le explico es que su voz se vuelve así ajá             ← 抱怨声音变来变去
坐席: Disculpe la mala conexión, Jorge. Le comento que la activación es
      gratis ... ¿Le gustaría que registre la activación?
用户: sí continúe ay señorita de ver es que este                  ← 模糊回应
坐席: Procedo a registrar la ac ...
用户: no sea no no entiendo lo que me dije mande                  ← "mande"=你说什么？
坐席: Claro, Jorge. Procedo a registrar la activación de su aumento de
      velocidad, ¿de acuerdo?
用户: pero este no puedo pagar más eh                             ← 突然清醒：付不起
坐席: Entiendo, Jorge. Recuerde q ...
用户: o sea tengo ahorita
坐席: Entiendo, Jorge. Recuerde que el costo adicional es solo 50 pesos
      mensuales ... ¿Desea que active la mejora ...?
用户: eh mire señorita la verdad no le entiendo pero este         ← 还是没懂
坐席: Una disculpa por la confusión, Jor ...
用户: el servicio como lo tengo ahorita es este mande             ← 又是"mande"
坐席: Claro, Jorge. Actualmente tiene 100 megas y con la promoción puede
      duplicar a 200 megas por solo 50 pesos más al mes. ... ¿Le gustaría
      probarlo?
用户: sí no señorita así como estoy estamos bien gracias yo le    ← 最终拒绝
      agradezco
坐席: Comprendo, Jorge. Solo recue ...
用户: la atención pero no así como estamos todos perfectamente bien
坐席: Entiendo, Jorge. Solo recuerde que con 100 megas adicionales podrá
      disfrutar mejor sus actividades en línea sin interrupciones. Pero si
      está satisfecho, le agradezco su tiempo. Que tenga un excelente día.
```

**注意力漂移轨迹**：听不清→又听清了→沉默→没听懂→拒绝→又没听懂→突然懂了→声音变了→"mande"→付不起→还是没懂→又是"mande"→拒绝。全程跳跃，坐席每句话他基本只听懂一半，回应经常脱节。

### 对话 #10 — 反复听不清（MegaCable 升速推销）

坐席重复多次，用户始终表示听不清，最终坐席放弃。

```
坐席: Si bueno buenas tardes, habla Vicky Robles de Mega. Tengo el gusto
      con HERMILA SOTO, ¿cierto?
用户: diga
坐席: Perfecto, Hermila. Mire hoy tenemos una promo que le aumenta 100
      megas a la velocidad de su internet por so ... [interrupted]
用户: no le escucho bien                                          ← 听不清
坐席: Disculpe, le comento que la promoción es un aumento de 100 megas a
      su velocidad actual de internet por solo 100 pesos mensuales. ¿Le
      cuento los detalles?
用户: no no no no le no le escucho señorita                       ← 连续"no"+还是听不清
坐席: Disculpe, ¿podría repetir lo que dijo con más detalle? No logro
      escucharlo bien.
用户: bueno
坐席: Una disculpa pero la línea se escucha un poco débil, ¿me puede
      confirmar si eso fue un sí?
用户: bueno no le no le entiendo bien lo que me dice porque       ← 听不清所以不明白
      no se escucha bien
坐席: ¿Sigue ahí? ¿Me escucha?
用户: bueno                                                       ← 单字回应
坐席: Una disculpa pero la línea se escucha un poco débil, ¿me puede
      confirmar si eso fue un sí?
用户: bueno                                                       ← 还是单字
坐席: Disculpa no puedo escucharte. Te llamaremos mas tarde, hasta luego.
```

**要点**：用户整个对话只说了两件事——"no le escucho"和"bueno"。坐席完全无法推进对话，最终放弃。典型的心不在焉+听不清场景。

---

## 六、情绪升级 / 愤怒

用户从礼貌拒绝升级到强调拒绝再到情绪化拒绝，或直接表达强烈不满。

### 对话 #11 — 经典三级情绪升级（MegaCable 升速推销）

```
坐席: ¿Bueno bueno?... muy buenas tardes DAVID FLORES. Habla Héctor
      Cárdenas de Mega, soy tu asesor personal en el área de promociones
      ¿cómo estás?
用户: bueno mire si es parame ofreceme un servicio ya les dije    ← 开场即升级
      que no yo estoy contento con lo que tengo contentísimo
      por favor ya no me estén marcando porque ya no quiero yo
      nada estoy bien con lo que tengo sí yo le agradezco
      mucho señor
坐席: Entiendo perfectamente, DAVID, y me alegra que estés contento con
      tu servicio actual... solo quería comentarte que hoy tengo una oferta
      especial para mejorar tu velocidad a 300 megas por solo 100 pesos
      extra ... ¿Te gustaría que te cuente un poco más?
用户: sí sí dale pues dale señor señor señor le vuelvo a repetir  ← 第2轮：讽刺性"dale"
      ya es como la que me están marcando y le dije que no me      + 威胁取消
      interesa no quiero ser grosero no me interesa gracias
      estoy contento ahora otra cosa si me siguen molestando
      mejor voy a renuniarr al al
坐席: Claro, DAVID, entiendo que te sientas así y no quiero incomodarte...
      solo imagina que con esos 300 megas podrías ver tus series sin
      cortes ... ¿No te gustaría probar esta mejora sin compromiso?
用户: a esa compañía por favor gracias pues ay                    ← 第3轮：放弃，直接对着公司说
坐席: Entiendo, DAVID, respeto mucho tu decisión y no te quitaré más
      tiempo. Gracias por tu tiempo, soy Héctor Cárdenas de Mega, ¡que
      tengas un gran día!
```

**递进轨迹**：第一句就是"ya les dije que no... por favor ya no me estén marcando"（开场即升级，说明之前已被骚扰多次）→ 第二句"señor señor señor le vuelvo a repetir... si me siguen molestando mejor voy a renunciar al"（反复叫"señor"+威胁取消服务）→ 第三句"a esa compañía por favor gracias pues ay"（直接对公司和坐席说，放弃沟通）。

### 对话 #12 — 被反复骚扰 + 决定取消（MegaCable 升速推销）

```
坐席: Muy buenas tardes AGUIÑAGA LUZ VIERE.
用户: buenas tardes
坐席: Que gusto saludarle, Luz. Soy Héctor Cárdenas, su asesor personal de
      promociones de Mega. Le llamo porque hoy tenemos una oferta exclusiva
      y está buenísima para ahorrar ¿Me permite contarle de qué se trata?
用户: no ya me han marcado muchas veces ya les dije que no         ← 第1轮：已被多次骚扰
      muchas gracias
坐席: Entiendo perfecto que a veces le quiten mucho tiempo con llamadas,
      pero si me regala unos segundos le cuento brevemente. Si no, no se
      preocupe le llamamos en otro momento.
用户: sí por favor gracias                                        ← 勉强同意
坐席: Su perfil fue seleccionado para una mejora de 100 megas adicionales
      en su servicio. ... ¿ha sentido que el internet se pone lento a veces,
      o que la señal no le llega bien?
用户: sí pero ya le dije ya me has marcado mejor me llaman en      ← 第2轮：再次强调已被骚扰
      otro momento por favor
坐席: Entiendo, Luz. Solo quiero recordarle que esta mejora no requiere
      visitas técnicas ... ¿Le gustaría aprovechar esta oportunidad hoy?
用户: no gracias                                                  ← 拒绝
坐席: Comprendo su punto sobre el costo ... ¿Le gustaría saber cómo sería?
用户: no gracias                                                  ← 再次拒绝
坐席: Es gratificante saber que está satisfecho con el servicio ... son
      solo 100 pesos adicionales ... ¿Le gustaría que activemos ...?
用户: no gracias así estoy bien gracias                           ← 第3轮：礼貌但坚定
坐席: Entiendo perfectamente y respeto su decisión. ... ¿Desea confirmar
      la activación?
用户: no gracias de hecho ya voy a cancelarme la ca               ← 终点：不光是拒绝，要取消
坐席: Entiendo. Igualmente le agradezco mucho su tiempo. Que tenga un
      excelente día.
```

**递进轨迹**："ya me han marcado muchas veces"（被多次骚扰）→ "ya le dije ya me has marcado"（强调已经说过了）→ "de hecho ya voy a cancelarme"（不止拒绝，要取消服务）。坐席的4轮推销每一次都让用户的愤怒级别上升一级。

---

## 七、转移决策权

用户声称自己不是决策者，需问配偶/子女/父母。实质是体面的拒绝方式。

### 对话 #13 — 反复推给妻子（MegaCable 满意度回访）

```
坐席: Si bueno buenas tardes
用户: bueno buenas tardes
坐席: Le atiende Karol Ferrer de Mega, su proveedor de internet. Le llamo
      brevemente para conocer cómo ha sido su experiencia con el servicio.
      Tengo el gusto con JOSE LUIS MAGAÑA, ¿correcto?
用户: sí bueno sí sí estamos este pues bien ahorita pues ahorita todavía
坐席: Gracias, José Luis. Mire, como hoy en día ya conectamos todo al
      internet, ... ¿cuál diría que es la que más pesa o donde ha llegado
      a notar que la velocidad ya no fluye igual ...?
用户: estado bien con el servicio sí este mire ahorita bueno yo    ← 我不常在家
      casi no estoy en la casa yo llego al ratito si en la noche
      sí casi no lo uso pero me ha comentado a mi esposa que
      está bien no sé                                               ← 引述妻子意见
坐席: Me da gusto que ahora le funcion ...
用户: si hay otra cosa que me diga mi esposo                       ← 妻管严：我老公说了算
坐席: Me da gusto que ahora le funcione bien en general. Para que disponga
      del mejor rendimiento ... hoy le puedo ofrecer duplicarle la velocidad
      a su servicio, por un costo de solo 50 pesos mensuales. ... ¿Qué le
      parece?
用户: sí con ella una hija que las que más que yo no estoy en      ← 家里老婆孩子用，我不在
      la casa no no no puedo yo decirle porque yo casi no lo
      uso yo casi no no estoy en la casa pero que
坐席: Entiendo, José Luis. Esta mejor ...
用户: que contar con ella es cómo están                            ← 得问她们
坐席: Entiendo, José Luis. Esta mejora le dará más potencia para que su
      esposa e hija puedan navegar ... ¿Le gustaría que le explique los
      detalles de la promoción?
用户: mmm creo yo que estamos bien así este le agradezco pero      ← 我们挺好的
      este ahorita no ha habido ningún pues no me han comentado
      nada de eso están pues bien creo bien porque no también
      casi no ven no tienen mucho tiempo de de estar ahí con
      internet
坐席: Entiendo que prefiera no actualizar su paquete. Pero piense en esto:
      con 100 megas adicionales por tan solo 50 pesos más al mes,
      asegurará el mejor rendimiento para su esposa e hija ...
      ¿Le gustaría que activemos la promoción ...?
用户: sí estamos que bien estamos bien así sí creo que estamos      ← 一直说"bien así"
      bien así no ha habido ningún
坐席: Comprendo que cuide su dinero. Ju ...
用户: ningún problema ni nada no me han comentado nada             ← 没人跟我说有问题
坐席: Comprendo que cuide su dinero. Justo por eso hoy le ofrezco la
      activación totalmente gratis ... ¿Le gustaría que registre la activación?
用户: sí                                                           ← 随口说"sí"
坐席: Procedo a registrar la ac ...
用户: no no puedo decidir de eso                                   ← 关键时刻：我不能决定
坐席: Entiendo, intentaremos comunicarnos más tarde. hasta luego.
用户: de eso no puedo recibir
坐席: Entiendo, intentaremos comunicarnos más tarde. hasta luego.
```

**要点**：用户全程将决策权推给不在场的妻子/女儿。开头"me ha comentado a mi esposa"，中间"no no no puedo yo decirle"，转折时刻"sí"（被动敷衍）→立刻收回"no no puedo decidir de eso"。最后"de eso no puedo recibir"——我不能接收这个决定。

### 对话 #14 — 推给丈夫（MegaCable 升速推销）

```
坐席: ¿Bueno bueno?... muy buenas tardes RAMONA ALEJANDRO. Habla Héctor
      Cárdenas de Mega, soy tu asesor personal en el área de promociones
      ¿cómo estás?
用户: muy bien gracias
坐席: ¡Qué bueno escucharlo, Ramona! Mira, hoy me autorizaron una
      oportunidad buenísima para tu perfil. Por ser cliente leal, te
      ofrezco aumentar tu velocidad a 300 megas por solo 100 pesos extra.
      ... ¿Te puedo contar más?
用户: ándele pues yo necesito contando con el que paga pues el     ← 开场就推：付钱的人说了算
      día el que paga yo no
坐席: Claro, Ramona, entiendo que el tema del pago es importante... ¿Usas
      mucho internet para ver series, trabajar o en familia? ...
用户: no casi no nomás somos aquí tres personas y o la te y el
      internet en los teléfonos es lo que máspamos pero no mucho no
坐席: Perfecto, Ramona, gracias ...
用户: mi señor pon a trabajar mi hija salió a trabajar y pues      ← 老公上班，女儿也上班
      no más yo me queedo
坐席: Entiendo, Ramona... entonces en ca ...
用户: y mi hija son el teléfono la tele                           ← 只有女儿用
坐席: Gracias por compartir, Ramona. Entonces, con esta promo tendrás 300
      megas, lo que significa que tanto tú como tu hija podrán usar el
      internet ... ¿Quieres que te la active hoy?
用户: no es que como le digo yo necesito hablar con mi esposo      ← 我需要跟老公说
      porque les sé que pagan este mes                              ← 这个月他们要付钱
坐席: Claro, Ramona, entiendo que qui ...
用户: y como les digo pues no
坐席: Entiendo, Ramona, que quieres ...
用户: no necesitamos tanto pues más como nosotros                  ← 我们不需要那么多
坐席: Entiendo tu duda, Ramona... No hay costo de contratación. Además,
      con los descuentos que te ofrezco ... ¿Te gustaría aprovecharlo?
用户: pues sí pero como le digo yo necesito contar cuando se paga  ← 我需要知道什么时候付钱
坐席: Claro, Ramona, el costo de 100 pesos se verá reflejado en la
      próxima factura que reciban ... ¿Quieres que te la active y después
      lo platicas con tu esposo?
用户: no no ahorita no                                             ← 明确拒绝
坐席: Entiendo tu decisión, Ramona... pero imagina cómo mejoraría la
      experiencia ... ¿Te animas a probar esta nueva experiencia cuando
      estés lista?
用户: sí pues cuando ya hablé yo con mi esposo si no llega la      ← 等我跟老公说了再说
      promoción pues ya lo hablé con él
坐席: Claro, Ramona, respeto que quieras hablarlo con tu esposo primero.
      Cuando estén listos, aquí estaré para ayudarte con la mejora. Te
      llamo otro día para ver cómo va todo, ¿te parece?
      Gracias por tu tiempo, soy Héctor Cárdenas de Mega, ¡que tengas un
      gran día!
用户: sí sí sí es
```

**要点**：全程以"el que paga"（付钱的人）为决策锚点。自己无法/不愿做决定，每次坐席试图close时都退回"necesito hablar con mi esposo"。最后"cuando ya hablé yo con mi esposo si no llega la promoción pues ya lo hablé con él"——即使促销过期也要先问老公。

---

## 八、拖延 / 软拒绝

不直接说"不"，用借口推迟。体面但实质性拒绝。坐席每次追问，用户换一种方式继续推。

### 对话 #15 — 7种变体拖延（MegaCable 流媒体推销）

```
坐席: Buenas tardes. le habla Karol Ferrer del área de promociones de
      Mega, ¡y le tengo buenas noticias! ¿hablo con María Gloria Carrillo,
      correcto?
用户: sí
坐席: Mire, por su preferencia con nosotros, queremos otorgarle los
      servicios de nétflix, áche beó máx, dísnei plós y ámazon práim con
      un costo especial! ... ¿Le gustaría que le comparta los detalles?
用户: sí hola
坐席: Es una oferta con ...
用户: ya ahorita no                                                ← 变体1
坐席: Entiendo que q ...
用户: ahorita no mejor después                                    ← 变体2
坐席: Entiendo que quiere cuidar su dinero ... ¿le gustaría confirmar la
      activación del servicio?
用户: no ahorita no gracias                                       ← 变体3
坐席: Entiendo que está satisfecho con los servicios que ya tiene. Pero
      esta experiencia de streaming le permitirá descubrir los títulos más
      exclusivos. ... ¿Le gustaría que le activáramos la promoción de
      inmediato para que la pruebe?
用户: sí no ahorita no después yo me comunico con ustedes          ← 变体4：我会联系你们
坐席: Le entiendo perfectamente y respeto su decisión. Solo le pido un
      minuto más, porque únicamente por hoy, al activar esta promoción,
      también le aumentaremos 50 megas a la velocidad de su paquete de
      internet completamente gratis. ¿Le confirmo la activación?
用户: gracias sí activ                                             ← 差一点中招
坐席: Perfecto, muchas gracias por confirmar la activación. No se
      requie ...
用户: mejor no la activación ahorita no mejor después para         ← 变体5：收回，继续推
      hasta cuándo está la promoción                                ← 还顺便问促销有效期
坐席: La promoción que le ofrecemos tiene un precio especial de 299 pesos
      mensuales, y es un precio fijo que no aumentará. Sin embargo, esta
      oferta es válida únicamente por hoy. ... ¿Le gustaría que le confirme
      la activación ahora?
用户: no tampoco no ahorita no por después                        ← 变体6
坐席: Enten ...
用户: todos modo muchas gracias                                    ← 变体7：总之谢谢
坐席: Entendido. muchas gracias por su tiempo. que tenga un excelente día.
用户: sí
坐席: Una disculpa, pero nuestra conversación ya no está relacionada ...
```

**递进轨迹**：ya ahorita no → ahorita no mejor después → no ahorita no gracias → después yo me comunico con ustedes → 差点激活马上收回"mejor no la activación ahorita no mejor después" → no tampoco no ahorita no por después → todos modo muchas gracias。7次推脱，每次措辞不同，核心策略不变：never say yes, always say later。

### 对话 #16 — 连续"ahorita no"（MegaCable Netflix推销）

```
坐席: Muy Buenas tardes. Le habla Maria Elena Rios de Mega, su proveedor
      de internet. Le contacto brevemente para revisar si podemos ayudarle
      a reducir costos en su factura. Tengo el gusto con MARIA GUADALUPE
      ARENAS, ¿correcto?
用户: sí
坐席: Gracias, María. Dígame, ¿actualmente cuenta con una suscripción de
      nétflix que pague por fuera? ¿Le gustaría que le ayudáramos a reducir
      ese gasto integrándolo a su paquete ...?
用户: no ahorita no porque yo no estoy allá y                      ← 第1次：不在家
坐席: Entiendo, María. ...
用户: me interesa porque no sé si vaya a poder ir ahorita pronto
坐席: Si no tiene cuenta, también le podemos apoyar con la contratación,
      para que empiece a disfrutar de todas sus películas y series
      favoritas por solo 110 pesos mensuales. Y de regalo le incluimos
      10 megas extra de velocidad. ¿Le explico cómo funcionaría?
用户: pues ahorita no me interesa ahorita                          ← 第2次
坐席: Comprendo totalmente, hoy más que nunca cuidamos cada peso. Por eso
      al activarlo con nosotros se ahorra el costo de suscripción externa
      ... ¿Le gustaría aprovechar este ahorro antes de que expire la campaña?
用户: sí mhm no ahorita no                                         ← 第3次
坐席: Entiendo que a veces el ritmo de vida no nos deja mucho tiempo para
      disfrutar de estos beneficios. Lo bonito de nétflix es que siempre
      hay algo de calidad ... ¿Le gustaría que le confirme la activación?
用户: no ahorita no                                                ← 第4次
坐席: Respeto su decisión. Solo me gustaría que no se perdiera esto porque
      es una oferta de un solo día: si lo activamos en este momento, no
      solo le queda nétflix en 110 pesos, sino que le regalamos 10 megas
      extra ... ¿Le confirmo la activación con este beneficio doble?
用户: no ahorita no                                                ← 第5次
坐席: Entiendo perfectamente. Muchas gracias por atender la llamada de
      Mega. Que tenga un excelente día.
用户: no ahorita no porque no me interesa sí                       ← 第6次：挂断后还在说
坐席: Le ofrezco una disculpa, pero nuestra conversación ya no está
      relacionada ...
```

**要点**：5次"ahorita no"，坐席每轮换一个理由（便宜、方便、限时、加赠），用户只回同一句话。最后挂断后还在重复"no ahorita no porque no me interesa sí"——已经形成肌肉记忆式的拒绝。

---

## 九、敷衍 / 极简

用户用最少的词回应，不提供额外信息，不配合引导。对自己没兴趣的事情说话很简短。

### 对话 #17 — 全是单音节（MegaCable 升速推销）

```
坐席: Muy buenas tardes. Que gusto saludarle, PEDRO GARCIA. Soy Héctor
      Cárdenas, su asesor de promos de Mega. Le llamo porque hoy tenemos
      una oferta exclusiva y está buenísima para ahorrar ¿Me permite
      contarle de qué se trata?
用户: sí                                                           ← 1词
坐席: Perfecto, PEDRO. Su perfil fue seleccionado para una mejora de 100
      megas adicionales en su servicio. ... ¿ha sentido que el internet se
      pone lento a veces, o que la señal no le llega bien?
用户: sí                                                           ← 1词
坐席: Justo para esas situaciones le traigo este beneficio: una oferta
      todo incluido por solo 100 pesos más al mes. ... ¿Desea activar su
      mejora?
用户: mhm                                                          ← 非语言声音
坐席: Entiendo, PEDRO. Comprendo su punto sobre el costo y lo tomamos en
      cuenta. Por eso hoy le ofrezco la activación gratis además de los
      descuentos por 300 pesos anuales. ... ¿Le gustaría saber cómo sería?
用户: sí                                                           ← 1词
坐席: <function-call> ... </function-call>
用户: <function-response>{"Current_plan_cost":680.0,...}
坐席: Claro, PEDRO. Actualmente su plan cuesta 680 pesos. Con la mejora,
      el costo sería de 780 pesos al mes. ... ¿Le gustaría que activemos
      la promoción ...?
用户: no                                                           ← 1词，首次拒绝
坐席: Entiendo, PEDRO. Es gratificante saber que está satisfecho con el
      servicio que le ofrecemos de 200 Megas. Pero son solo 100 pesos
      adicionales ... ¿Le gustaría que activemos la promoción ...?
用户: no                                                           ← 1词
坐席: Comprendo perfectamente, PEDRO. Esta tarifa preferencial ... es una
      oferta temporal. Si no la activa hoy no puedo garantizarle que esté
      disponible después. ¿Desea confirmar la activación?
```

**发言记录**：sí → sí → mhm → sí → no → no。全程没有一个超过1个词的回复。不提问、不解释、不提供任何信息。坐席在对着一个黑洞推销。

### 对话 #18 — 连续5个"no"（MegaCable 流媒体推销）

```
坐席: Si bueno muy buenas tardes
用户: bueno                                                        ← 唯一不是no的回复
坐席: Le habla Karol Ferrer de Mega, su proveedor de internet. Le contacto
      brevemente para revisar si podemos ayudarle a reducir costos en su
      factura. Hablo con JAVIER ALVAREZ, ¿correcto?
用户: sí                                                           ← 1词
坐席: Gracias, Javier. Dígame, ¿actualmente cuenta con una suscripción de
      nétflix, áche beó máx, dísnei plós o ámazon práim que pague por
      fuera? ¿Le gustaría que le ayudáramos a reducir ese gasto ...?
用户: no                                                           ← 第1个no
坐席: ¡Mire, le ofrecemos nétflix, áche beó máx, dísnei plós y ámazon
      práim por solo 299 pesos al mes! Para que disfrute sus series y
      películas favoritas. ¿Quiere que le cuente los detalles?
用户: no                                                           ← 第2个no
坐席: Comprendo que cuide su dinero. Justamente por eso este descuento le
      dará acceso a las cuatro mejores plataformas de streaming sin pagar
      de más. ¿Lo activamos?
用户: no                                                           ← 第3个no
坐席: Entiendo que está satisfecho con los servicios que ya tiene. Pero
      esta experiencia de streaming le permitirá descubrir títulos
      exclusivos como Berlín, El Pingüino, ex-Men '97, The Boys ...
      ¿Lo activamos ya?
用户: no                                                           ← 第4个no
坐席: Respeto su decisión, solo le comento que al tomar esta oferta hoy,
      recibe además 50 megas extra en su internet totalmente gratis.
      ¿Lo activamos?
用户: no                                                           ← 第5个no
坐席: Entendido. Muchas gracias por su tiempo. Que tenga un excelente día.
```

**发言记录**：bueno → sí → no → no → no → no → no。坐席换了4种推销角度（省钱、内容丰富、热门片单、加赠），用户用同一个"no"回应全部。不在意你换了什么话术，也不解释为什么拒绝。

---

## 中西语风格对照

真实语料为西语，但口语模式跨语言通用。生成中文 user profile 时按以下映射转化：

| 西语特征 | 西语示例 | 中文等价 |
|----------|---------|----------|
| 直接拒绝 | "no me interesa""así estoy bien" | "我不需要""算了吧""就这样吧" |
| 填充词/口水词 | "bueno""pues""este""eh""mmm" | "那个""就是""嗯""啊""反正""怎么说呢" |
| 防备试探 | "de dónde habla""quién habla""de qué compañía" | "你哪里的""你怎么有我电话""谁给你的号码" |
| 不耐烦 | "estoy ocupado""estoy trabajando""me regañan""tengo que colgar" | "我在忙""上班呢""被骂的""挂了" |
| 讨价还价 | "cuánto sería""más barato""cuánto pagaría por todo" | "多少钱""能不能便宜""一共多少" |
| 敷衍极简 | "bueno""ajá""sí""no""mhm" | "嗯""哦""行吧""不" |
| 拖延 | "ahorita no""mejor después""luego""otra ocasión" | "下次吧""改天""回头再说""到时候我联系你" |
| 转移决策 | "mi esposo""hablar con mi hijo""el que paga" | "我问问我老公""孩子说了算""付钱的人决定" |
| 走神 | "mande""no le escuché""no le entendí""casi no la escucho" | "啊？""你说什么？""没听清""信号不好" |
| 情绪升级 | "ya les dije""no entienden""mejor voy a cancelar" | "我都说了不要""你听不懂吗""我要取消" |
| 身份锚定 | "somos dos personas adultas""no lo usamos" | "我们老年人不用的""家里没人看这个" |
| 经济摊牌 | "la economía está caramba""estoy pagando mucho" | "经济不好""我付太多了""真没钱" |

语言差异注意：
- 西语用户常用反问和重复加强拒绝，中文用户更习惯用沉默/"算了"表达放弃
- 西语 "no gracias" 是高频礼貌拒绝句式，中文更常直接说"不用了""我不需要"
- 中文口语更频繁省略主语（"那个...就是...反正不太合适"）

---

## 使用指南

生成 user profile 的 task_instructions 时，参考上述完整对话来编写用户的具体台词。原则：

1. **参考完整对话的递进结构**——行为不是一次性的，而是逐轮升级的：
   - 直接拒绝型：第1轮简短拒绝 → 第2轮加理由 → 第3轮身份锚定或经济摊牌
   - 防备质疑型：先核实身份（可能多次追问）→ 确认后立刻找理由拒绝
   - 不耐烦型：说忙→说会被骂→连续拒绝→主动挂断
   - 拖延型：每次换一个借口推脱，不变的是永远不说yes
   - 情绪升级型：礼貌拒绝→强调已说过→引用被骚扰经历→威胁取消
   - 转移决策型：全程以不在场的人为决策锚点，自己"不能决定"

2. **不照抄，学模式**——参考语料的语气、句式结构、递进节奏，按上表改写为中文

3. **保持口语破碎感**——真实用户说话破碎、重复、带口头禅。注意"de de dónde habla"这种口吃式重复、"[interrupted]"打断标记、模糊表达"no sé""este..."等

4. **控制长度**——真实用户单次发言通常 5~30 词（中文约 10~50 字），极少超过 50 词。敷衍型用户更是单次1~3词

5. **混入口癖**——中文用"那个""就是""嗯""啊""反正""怎么说呢"，参考上表的中西对照

6. **体现动态变化**——用户状态随对话进程改变：
   - 如果客服命中了利益点，注意力会被短暂拉回（如走神对话#9中的"ahí sí le entendí"）
   - 如果用户没什么兴趣，会快速变得敷衍、抗拒直至挂断，且几乎不可逆
   - 无诉求时完全被动，持续敷衍、极简回答、沉默或直接挂断
   - 有诉求时主动打断，以自己的利益为中心
